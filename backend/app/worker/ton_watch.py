from __future__ import annotations

import logging
from datetime import datetime, timezone
from decimal import Decimal

from sqlmodel import Session, select

from app.domain.escrow_fsm import EscrowState, EscrowTransitionError, apply_escrow_transition
from app.models.deal import Deal, DealState
from app.models.deal_escrow import DealEscrow
from app.models.escrow_event import EscrowEvent
from app.services.bot_notifications import notify_deal_funded
from app.services.deal_fsm import DealAction, DealActorRole, DealTransitionError, apply_transition
from app.services.ton.chain_scan import TonCenterAdapter, TonChainAdapter
from app.services.ton.errors import TonConfigError
from app.settings import get_settings
from app.worker.celery_app import celery_app
from shared.db.session import SessionLocal

logger = logging.getLogger(__name__)


def _known_tx_hashes(db: Session, escrow_id: int) -> set[str]:
    events = db.exec(
        select(EscrowEvent)
        .where(EscrowEvent.escrow_id == escrow_id)
        .where(EscrowEvent.event_type == "tx_seen")
    ).all()
    hashes: set[str] = set()
    for event in events:
        payload = event.payload or {}
        if isinstance(payload, dict) and payload.get("tx_hash"):
            hashes.add(str(payload["tx_hash"]))
    return hashes


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


def _process_escrow(
    *,
    db: Session,
    escrow: DealEscrow,
    adapter: TonChainAdapter,
    settings,
) -> None:
    if escrow.deposit_address is None or escrow.expected_amount_ton is None:
        return

    if escrow.state not in {EscrowState.AWAITING_DEPOSIT.value, EscrowState.DEPOSIT_DETECTED.value}:
        return

    known_hashes = _known_tx_hashes(db, escrow.id)
    since_lt = _last_seen_lt(db, escrow.id)
    new_txs: list[dict] = []
    updated = False

    while True:
        tx = adapter.find_incoming_tx(
            escrow.deposit_address,
            Decimal("0"),
            since_lt,
        )
        if tx is None:
            break
        tx_hash = tx.get("hash")
        if tx_hash and str(tx_hash) not in known_hashes:
            new_txs.append(tx)
            known_hashes.add(str(tx_hash))
        since_lt = str(tx.get("lt")) if tx.get("lt") is not None else since_lt
        if since_lt is None:
            break

    for tx in new_txs:
        tx_hash = str(tx.get("hash"))
        amount_ton = tx.get("amount_ton")
        if amount_ton is None:
            continue
        escrow.received_amount_ton = (escrow.received_amount_ton or Decimal("0")) + Decimal(amount_ton)
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

    if (
        escrow.received_amount_ton is not None
        and escrow.expected_amount_ton is not None
        and escrow.received_amount_ton >= escrow.expected_amount_ton
        and escrow.deposit_confirmations >= settings.TON_CONFIRMATIONS_REQUIRED
        and escrow.state == EscrowState.DEPOSIT_DETECTED.value
    ):
        apply_escrow_transition(
            db,
            escrow=escrow,
            to_state=EscrowState.FUNDED.value,
            actor_user_id=None,
            event_type="confirmed",
            payload={"confirmations": escrow.deposit_confirmations},
        )

        deal = db.exec(select(Deal).where(Deal.id == escrow.deal_id)).first()
        if deal is None:
            raise ValueError("Deal not found for escrow")

        if deal.state == DealState.CREATIVE_APPROVED.value:
            if deal.scheduled_at is None:
                # Keep legacy flows moving: no explicit schedule means "post as soon as funded".
                deal.scheduled_at = datetime.now(timezone.utc)
                db.add(deal)
            apply_transition(
                db,
                deal=deal,
                action=DealAction.fund.value,
                actor_id=None,
                actor_role=DealActorRole.system.value,
                payload={"escrow_id": escrow.id},
            )
            notify_deal_funded(db=db, settings=settings, deal=deal)


@celery_app.task(name="app.worker.ton_watch.scan_escrows")
def scan_escrows() -> int:
    settings = get_settings()
    if not settings.TON_ENABLED:
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
            except (TonConfigError, EscrowTransitionError, DealTransitionError, ValueError) as exc:
                logger.error("Escrow watch failed", extra={"escrow_id": escrow.id, "error": str(exc)})
                db.rollback()
                continue
            else:
                db.commit()
                processed += 1

    return processed
