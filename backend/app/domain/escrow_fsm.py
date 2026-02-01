from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

from sqlmodel import Session

from app.models.deal_escrow import DealEscrow
from app.models.escrow_event import EscrowEvent


class EscrowState(str, Enum):
    CREATED = "CREATED"
    AWAITING_DEPOSIT = "AWAITING_DEPOSIT"
    DEPOSIT_DETECTED = "DEPOSIT_DETECTED"
    FUNDED = "FUNDED"
    FAILED = "FAILED"


TRANSITIONS: set[tuple[str, str]] = {
    (EscrowState.CREATED.value, EscrowState.AWAITING_DEPOSIT.value),
    (EscrowState.AWAITING_DEPOSIT.value, EscrowState.DEPOSIT_DETECTED.value),
    (EscrowState.DEPOSIT_DETECTED.value, EscrowState.FUNDED.value),
    (EscrowState.CREATED.value, EscrowState.FAILED.value),
    (EscrowState.AWAITING_DEPOSIT.value, EscrowState.FAILED.value),
    (EscrowState.DEPOSIT_DETECTED.value, EscrowState.FAILED.value),
}


class EscrowTransitionError(ValueError):
    pass


def apply_escrow_transition(
    db: Session,
    *,
    escrow: DealEscrow,
    to_state: str,
    actor_user_id: int | None,
    event_type: str,
    payload: dict | None = None,
) -> DealEscrow:
    if escrow.id is None:
        raise EscrowTransitionError("Escrow must be persisted before transition")

    if (escrow.state, to_state) not in TRANSITIONS:
        raise EscrowTransitionError("Escrow transition not allowed")

    from_state = escrow.state
    escrow.state = to_state
    escrow.updated_at = datetime.now(timezone.utc)

    event = EscrowEvent(
        escrow_id=escrow.id,
        actor_user_id=actor_user_id,
        from_state=from_state,
        to_state=to_state,
        event_type=event_type,
        payload=payload or None,
    )
    db.add(event)
    db.add(escrow)
    return escrow
