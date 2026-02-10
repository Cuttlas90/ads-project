from __future__ import annotations

import logging
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.domain.escrow_fsm import EscrowState, EscrowTransitionError, apply_escrow_transition
from app.models.deal import Deal, DealState
from app.models.deal_escrow import DealEscrow
from app.models.deal_event import DealEvent
from app.models.escrow_event import EscrowEvent
from app.models.user import User
from app.services.bot_notifications import notify_deal_funded
from app.services.deal_fsm import DealAction, DealActorRole, DealTransitionError, apply_transition
from app.services.ton.addressing import to_raw_address
from app.services.ton.chain_scan import TonCenterAdapter, TonChainAdapter
from app.services.ton.errors import TonConfigError
from app.services.ton.payouts import PayoutError, ensure_refund
from app.settings import get_settings
from app.worker.celery_app import celery_app
from shared.db.session import SessionLocal

logger = logging.getLogger(__name__)


def _ensure_aware_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _parse_start_at(value: object) -> datetime | None:
    if isinstance(value, datetime):
        return _ensure_aware_utc(value)
    if not isinstance(value, str):
        return None

    candidate = value.strip()
    if not candidate:
        return None
    if candidate.endswith("Z"):
        candidate = candidate[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(candidate)
    except ValueError:
        return None
    return _ensure_aware_utc(parsed)


def _latest_negotiated_start_at(db: Session, deal_id: int) -> datetime | None:
    payload = (
        db.exec(
            select(DealEvent.payload)
            .where(DealEvent.deal_id == deal_id)
            .where(DealEvent.event_type == "proposal")
            .order_by(DealEvent.created_at.desc(), DealEvent.id.desc())
        )
        .first()
    )
    if not isinstance(payload, dict):
        return None
    return _parse_start_at(payload.get("start_at"))


def _effective_start_at(db: Session, deal: Deal) -> datetime | None:
    if deal.scheduled_at is not None:
        return _ensure_aware_utc(deal.scheduled_at)
    return _latest_negotiated_start_at(db, deal.id)


def _known_tx_keys(db: Session, escrow_id: int) -> set[str]:
    events = db.exec(
        select(EscrowEvent)
        .where(EscrowEvent.escrow_id == escrow_id)
        .where(EscrowEvent.event_type == "tx_seen")
    ).all()
    keys: set[str] = set()
    for event in events:
        payload = event.payload or {}
        if not isinstance(payload, dict):
            continue
        tx_hash = payload.get("tx_hash")
        if tx_hash:
            keys.add(f"h:{tx_hash}")
        lt = payload.get("lt")
        if lt is not None:
            try:
                keys.add(f"l:{int(lt)}")
            except (TypeError, ValueError):
                continue
    return keys


def _tx_dedup_keys(tx: dict) -> set[str]:
    keys: set[str] = set()
    tx_hash = tx.get("hash")
    if tx_hash:
        keys.add(f"h:{tx_hash}")
    lt = tx.get("lt")
    if lt is not None:
        try:
            keys.add(f"l:{int(lt)}")
        except (TypeError, ValueError):
            pass
    return keys


def _last_seen_lt(db: Session, escrow_id: int) -> str | None:
    events = db.exec(
        select(EscrowEvent)
        .where(EscrowEvent.escrow_id == escrow_id)
        .where(EscrowEvent.event_type == "tx_seen")
    ).all()
    lts: list[int] = []
    for event in events:
        payload = event.payload or {}
        if isinstance(payload, dict) and payload.get("lt") is not None:
            try:
                lts.append(int(payload["lt"]))
            except (TypeError, ValueError):
                continue
    if not lts:
        return None
    return str(max(lts))


def _timeout_close(
    *,
    db: Session,
    escrow: DealEscrow,
    deal: Deal,
    settings,
) -> bool:
    effective_start_at = _effective_start_at(db, deal)
    if effective_start_at is None:
        return False
    now = datetime.now(timezone.utc)
    if now < effective_start_at:
        return False

    apply_escrow_transition(
        db,
        escrow=escrow,
        to_state=EscrowState.FAILED.value,
        actor_user_id=None,
        event_type="funding_timeout",
        payload={
            "effective_start_at": effective_start_at.isoformat(),
            "received_amount_ton": str(escrow.received_amount_ton or Decimal("0")),
            "expected_amount_ton": str(escrow.expected_amount_ton or Decimal("0")),
        },
    )

    if deal.state == DealState.CREATIVE_APPROVED.value:
        apply_transition(
            db,
            deal=deal,
            action=DealAction.refund.value,
            actor_id=None,
            actor_role=DealActorRole.system.value,
            payload={
                "reason": "funding_timeout",
                "effective_start_at": effective_start_at.isoformat(),
                "escrow_id": escrow.id,
            },
        )

    if (escrow.received_amount_ton or Decimal("0")) > 0:
        advertiser = db.exec(select(User).where(User.id == deal.advertiser_id)).first()
        if advertiser is None:
            raise ValueError("Advertiser not found for timeout refund")
        ensure_refund(
            db=db,
            deal=deal,
            escrow=escrow,
            advertiser=advertiser,
            settings=settings,
        )
    else:
        escrow.refunded_amount_ton = Decimal("0.000000000")
        escrow.refunded_at = now
        db.add(escrow)

    return True


def _required_worker_settings(settings) -> list[str]:
    missing: list[str] = []
    if not settings.TONCENTER_API:
        missing.append("TONCENTER_API")
    if not settings.TON_HOT_WALLET_MNEMONIC:
        missing.append("TON_HOT_WALLET_MNEMONIC")
    return missing


def _process_escrow(
    *,
    db: Session,
    escrow: DealEscrow,
    adapter: TonChainAdapter,
    settings,
) -> None:
    if escrow.expected_amount_ton is None:
        return

    if escrow.state not in {EscrowState.AWAITING_DEPOSIT.value, EscrowState.DEPOSIT_DETECTED.value}:
        return

    deal = db.exec(select(Deal).where(Deal.id == escrow.deal_id)).first()
    if deal is None:
        raise ValueError("Deal not found for escrow")

    if not escrow.deposit_address_raw and escrow.deposit_address:
        escrow.deposit_address_raw = to_raw_address(escrow.deposit_address)
        db.add(escrow)

    watch_address = escrow.deposit_address_raw or escrow.deposit_address
    if not watch_address:
        return

    known_keys = _known_tx_keys(db, escrow.id)
    since_lt = _last_seen_lt(db, escrow.id)
    new_txs: list[dict] = []
    updated = False

    while True:
        tx = adapter.find_incoming_tx(
            watch_address,
            Decimal("0"),
            since_lt,
        )
        if tx is None:
            break

        tx_keys = _tx_dedup_keys(tx)
        since_lt = str(tx.get("lt")) if tx.get("lt") is not None else since_lt
        if tx_keys and tx_keys.isdisjoint(known_keys):
            new_txs.append(tx)
            known_keys.update(tx_keys)

        if since_lt is None:
            break

    for tx in new_txs:
        tx_hash = str(tx.get("hash")) if tx.get("hash") is not None else None
        amount_ton = tx.get("amount_ton")
        if amount_ton is None:
            continue

        escrow.received_amount_ton = (escrow.received_amount_ton or Decimal("0")) + Decimal(amount_ton)
        if tx_hash:
            escrow.deposit_tx_hash = tx_hash
        updated = True

        db.add(
            EscrowEvent(
                escrow_id=escrow.id,
                actor_user_id=None,
                from_state=None,
                to_state=escrow.state,
                event_type="tx_seen",
                payload={
                    "tx_hash": tx_hash,
                    "amount_ton": str(amount_ton),
                    "lt": tx.get("lt"),
                    "utime": tx.get("utime"),
                    "mc_block_seqno": tx.get("mc_block_seqno"),
                },
            )
        )

    if new_txs and escrow.state == EscrowState.AWAITING_DEPOSIT.value:
        apply_escrow_transition(
            db,
            escrow=escrow,
            to_state=EscrowState.DEPOSIT_DETECTED.value,
            actor_user_id=None,
            event_type="deposit_detected",
            payload={"tx_count": len(new_txs)},
        )

    if escrow.deposit_tx_hash:
        confirmations = adapter.get_confirmations(escrow.deposit_tx_hash)
        if confirmations != escrow.deposit_confirmations:
            escrow.deposit_confirmations = confirmations
            updated = True

    if updated:
        escrow.updated_at = datetime.now(timezone.utc)

    is_funded = (
        escrow.received_amount_ton is not None
        and escrow.expected_amount_ton is not None
        and escrow.received_amount_ton >= escrow.expected_amount_ton
        and escrow.deposit_confirmations >= settings.TON_CONFIRMATIONS_REQUIRED
        and escrow.state == EscrowState.DEPOSIT_DETECTED.value
    )

    if is_funded:
        apply_escrow_transition(
            db,
            escrow=escrow,
            to_state=EscrowState.FUNDED.value,
            actor_user_id=None,
            event_type="confirmed",
            payload={"confirmations": escrow.deposit_confirmations},
        )

        if deal.state == DealState.CREATIVE_APPROVED.value:
            apply_transition(
                db,
                deal=deal,
                action=DealAction.fund.value,
                actor_id=None,
                actor_role=DealActorRole.system.value,
                payload={"escrow_id": escrow.id},
            )
            notify_deal_funded(db=db, settings=settings, deal=deal)
        return

    if deal.state == DealState.CREATIVE_APPROVED.value:
        _timeout_close(db=db, escrow=escrow, deal=deal, settings=settings)


@celery_app.task(name="app.worker.ton_watch.scan_escrows")
def scan_escrows() -> int:
    settings = get_settings()
    if not settings.TON_ENABLED:
        return 0

    missing = _required_worker_settings(settings)
    if missing:
        logger.error(
            "TON escrow watcher misconfigured",
            extra={"missing_settings": missing},
        )
        return 0

    adapter = TonCenterAdapter(settings)
    processed = 0

    with SessionLocal() as db:
        escrows = db.exec(
            select(DealEscrow).where(
                DealEscrow.state.in_(
                    [EscrowState.AWAITING_DEPOSIT.value, EscrowState.DEPOSIT_DETECTED.value]
                )
            )
        ).all()

        for escrow in escrows:
            try:
                _process_escrow(db=db, escrow=escrow, adapter=adapter, settings=settings)
            except (
                IntegrityError,
                TonConfigError,
                EscrowTransitionError,
                DealTransitionError,
                PayoutError,
                ValueError,
            ) as exc:
                logger.error("Escrow watch failed", extra={"escrow_id": escrow.id, "error": str(exc)})
                db.rollback()
                continue
            else:
                db.commit()
                processed += 1

    return processed
