from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, ROUND_DOWN

from sqlmodel import Session

from app.models.deal import Deal, DealState
from app.models.deal_escrow import DealEscrow
from app.models.user import User
from app.services.deal_fsm import DealAction, DealActorRole, apply_transition
from app.services.ton.errors import TonConfigError
from app.services.ton.transfers import TonTransferError, send_ton_transfer
from app.settings import Settings

_ZERO = Decimal("0")


class PayoutError(RuntimeError):
    pass


@dataclass(frozen=True)
class PayoutResult:
    tx_hash: str
    amount_ton: Decimal


def _quantize_amount(amount: Decimal) -> Decimal:
    return amount.quantize(Decimal("0.000000001"), rounding=ROUND_DOWN)


def calculate_release_amount(amount_ton: Decimal, fee_percent: Decimal, network_fee: Decimal) -> Decimal:
    fee = (amount_ton * fee_percent / Decimal("100")).quantize(Decimal("0.000000001"), rounding=ROUND_DOWN)
    return _quantize_amount(amount_ton - fee - network_fee)


def calculate_refund_amount(amount_ton: Decimal, network_fee: Decimal) -> Decimal:
    return _quantize_amount(amount_ton - network_fee)


def _settlement_principal(*, deal: Deal, escrow: DealEscrow) -> Decimal:
    expected = escrow.expected_amount_ton if escrow.expected_amount_ton is not None else deal.price_ton
    received = escrow.received_amount_ton if escrow.received_amount_ton is not None else _ZERO
    if expected is None:
        expected = _ZERO
    return _quantize_amount(min(Decimal(expected), Decimal(received)))


def _require_wallet(user: User) -> str:
    if not user.ton_wallet_address:
        raise PayoutError("User wallet address is missing")
    return user.ton_wallet_address


def release_funds(
    *,
    db: Session,
    deal: Deal,
    escrow: DealEscrow,
    owner: User,
    settings: Settings,
    transfer_fn=send_ton_transfer,
) -> PayoutResult:
    if deal.state != DealState.VERIFIED.value:
        raise PayoutError("Deal is not verified")
    if escrow.release_tx_hash:
        raise PayoutError("Release already processed")

    wallet = _require_wallet(owner)
    if settings.TON_FEE_PERCENT is None:
        raise PayoutError("TON_FEE_PERCENT is not configured")

    principal = _settlement_principal(deal=deal, escrow=escrow)
    amount = calculate_release_amount(principal, settings.TON_FEE_PERCENT, settings.TON_REFUND_NETWORK_FEE)
    if amount <= 0:
        escrow.released_amount_ton = _quantize_amount(_ZERO)
        escrow.released_at = datetime.now(timezone.utc)
        db.add(escrow)

        apply_transition(
            db,
            deal=deal,
            action=DealAction.release.value,
            actor_id=None,
            actor_role=DealActorRole.system.value,
            payload={"escrow_id": escrow.id, "release_tx_hash": None, "release_skipped": "non_positive_amount"},
        )
        return PayoutResult(tx_hash="", amount_ton=escrow.released_amount_ton)

    try:
        tx_hash = transfer_fn(
            settings=settings,
            to_address=wallet,
            amount_ton=amount,
            source_subwallet_id=escrow.subwallet_id,
        )
    except (TonTransferError, TonConfigError) as exc:
        raise PayoutError(str(exc)) from exc

    escrow.release_tx_hash = tx_hash
    escrow.released_amount_ton = amount
    escrow.released_at = datetime.now(timezone.utc)
    db.add(escrow)

    apply_transition(
        db,
        deal=deal,
        action=DealAction.release.value,
        actor_id=None,
        actor_role=DealActorRole.system.value,
        payload={"escrow_id": escrow.id, "release_tx_hash": tx_hash},
    )

    return PayoutResult(tx_hash=tx_hash, amount_ton=amount)


def refund_funds(
    *,
    db: Session,
    deal: Deal,
    escrow: DealEscrow,
    advertiser: User,
    settings: Settings,
    transfer_fn=send_ton_transfer,
) -> PayoutResult:
    if deal.state != DealState.REFUNDED.value:
        raise PayoutError("Deal is not marked for refund")
    if escrow.refund_tx_hash:
        raise PayoutError("Refund already processed")

    wallet = _require_wallet(advertiser)
    principal = _settlement_principal(deal=deal, escrow=escrow)
    amount = calculate_refund_amount(principal, settings.TON_REFUND_NETWORK_FEE)
    if amount <= 0:
        escrow.refunded_amount_ton = _quantize_amount(_ZERO)
        escrow.refunded_at = datetime.now(timezone.utc)
        db.add(escrow)
        return PayoutResult(tx_hash="", amount_ton=escrow.refunded_amount_ton)

    try:
        tx_hash = transfer_fn(
            settings=settings,
            to_address=wallet,
            amount_ton=amount,
            source_subwallet_id=escrow.subwallet_id,
        )
    except (TonTransferError, TonConfigError) as exc:
        raise PayoutError(str(exc)) from exc

    escrow.refund_tx_hash = tx_hash
    escrow.refunded_amount_ton = amount
    escrow.refunded_at = datetime.now(timezone.utc)
    db.add(escrow)

    return PayoutResult(tx_hash=tx_hash, amount_ton=amount)


def ensure_release(
    *,
    db: Session,
    deal: Deal,
    escrow: DealEscrow,
    owner: User,
    settings: Settings,
    transfer_fn=send_ton_transfer,
) -> PayoutResult | None:
    if escrow.release_tx_hash or escrow.released_at is not None:
        return None
    return release_funds(
        db=db,
        deal=deal,
        escrow=escrow,
        owner=owner,
        settings=settings,
        transfer_fn=transfer_fn,
    )


def ensure_refund(
    *,
    db: Session,
    deal: Deal,
    escrow: DealEscrow,
    advertiser: User,
    settings: Settings,
    transfer_fn=send_ton_transfer,
) -> PayoutResult | None:
    if escrow.refund_tx_hash or escrow.refunded_at is not None:
        return None
    return refund_funds(
        db=db,
        deal=deal,
        escrow=escrow,
        advertiser=advertiser,
        settings=settings,
        transfer_fn=transfer_fn,
    )
