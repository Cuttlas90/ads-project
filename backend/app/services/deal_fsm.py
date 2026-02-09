from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum

from sqlmodel import Session

from app.models.deal import Deal, DealState
from app.models.deal_event import DealEvent


class DealActorRole(str, Enum):
    advertiser = "advertiser"
    channel_owner = "channel_owner"
    system = "system"


class DealAction(str, Enum):
    advance = "advance"
    propose = "propose"
    accept = "accept"
    reject = "reject"
    creative_submit = "creative_submit"
    creative_approve = "creative_approve"
    creative_request_edits = "creative_request_edits"
    fund = "fund"
    schedule = "schedule"
    post = "post"
    verify = "verify"
    release = "release"
    refund = "refund"


@dataclass(frozen=True)
class TransitionSpec:
    to_state: str
    allowed_roles: set[str]


TRANSITIONS: dict[tuple[str, str], TransitionSpec] = {
    (DealAction.advance.value, DealState.DRAFT.value): TransitionSpec(
        DealState.NEGOTIATION.value,
        {DealActorRole.system.value},
    ),
    (DealAction.propose.value, DealState.DRAFT.value): TransitionSpec(
        DealState.NEGOTIATION.value,
        {DealActorRole.advertiser.value, DealActorRole.channel_owner.value},
    ),
    (DealAction.propose.value, DealState.NEGOTIATION.value): TransitionSpec(
        DealState.NEGOTIATION.value,
        {DealActorRole.advertiser.value, DealActorRole.channel_owner.value},
    ),
    (DealAction.accept.value, DealState.DRAFT.value): TransitionSpec(
        DealState.CREATIVE_APPROVED.value,
        {DealActorRole.advertiser.value, DealActorRole.channel_owner.value},
    ),
    (DealAction.accept.value, DealState.NEGOTIATION.value): TransitionSpec(
        DealState.CREATIVE_APPROVED.value,
        {DealActorRole.advertiser.value, DealActorRole.channel_owner.value},
    ),
    (DealAction.creative_submit.value, DealState.ACCEPTED.value): TransitionSpec(
        DealState.CREATIVE_SUBMITTED.value,
        {DealActorRole.channel_owner.value},
    ),
    (DealAction.creative_submit.value, DealState.CREATIVE_CHANGES_REQUESTED.value): TransitionSpec(
        DealState.CREATIVE_SUBMITTED.value,
        {DealActorRole.channel_owner.value},
    ),
    (DealAction.creative_approve.value, DealState.CREATIVE_SUBMITTED.value): TransitionSpec(
        DealState.CREATIVE_APPROVED.value,
        {DealActorRole.advertiser.value},
    ),
    (DealAction.creative_request_edits.value, DealState.CREATIVE_SUBMITTED.value): TransitionSpec(
        DealState.CREATIVE_CHANGES_REQUESTED.value,
        {DealActorRole.advertiser.value},
    ),
    (DealAction.fund.value, DealState.CREATIVE_APPROVED.value): TransitionSpec(
        DealState.FUNDED.value,
        {DealActorRole.system.value},
    ),
    (DealAction.schedule.value, DealState.FUNDED.value): TransitionSpec(
        DealState.SCHEDULED.value,
        {DealActorRole.system.value},
    ),
    (DealAction.post.value, DealState.SCHEDULED.value): TransitionSpec(
        DealState.POSTED.value,
        {DealActorRole.system.value},
    ),
    (DealAction.verify.value, DealState.POSTED.value): TransitionSpec(
        DealState.VERIFIED.value,
        {DealActorRole.system.value},
    ),
    (DealAction.release.value, DealState.VERIFIED.value): TransitionSpec(
        DealState.RELEASED.value,
        {DealActorRole.system.value},
    ),
    (DealAction.refund.value, DealState.POSTED.value): TransitionSpec(
        DealState.REFUNDED.value,
        {DealActorRole.system.value},
    ),
    (DealAction.reject.value, DealState.DRAFT.value): TransitionSpec(
        DealState.REJECTED.value,
        {DealActorRole.advertiser.value, DealActorRole.channel_owner.value},
    ),
    (DealAction.reject.value, DealState.NEGOTIATION.value): TransitionSpec(
        DealState.REJECTED.value,
        {DealActorRole.advertiser.value, DealActorRole.channel_owner.value},
    ),
}


class DealTransitionError(ValueError):
    pass


def apply_transition(
    db: Session,
    *,
    deal: Deal,
    action: str,
    actor_id: int | None,
    actor_role: str,
    payload: dict | None = None,
) -> Deal:
    if deal.id is None:
        raise DealTransitionError("Deal must be persisted before transition")

    transition = TRANSITIONS.get((action, deal.state))
    if transition is None:
        raise DealTransitionError("Transition not allowed")

    if actor_role not in transition.allowed_roles:
        raise DealTransitionError("Actor role not allowed")

    if actor_role != DealActorRole.system.value and actor_id is None:
        raise DealTransitionError("Actor id required for non-system transitions")

    if actor_role == DealActorRole.system.value and actor_id is not None:
        raise DealTransitionError("System transitions must not include actor id")

    from_state = deal.state
    deal.state = transition.to_state
    deal.updated_at = datetime.now(timezone.utc)

    event_payload = dict(payload or {})
    event_payload.setdefault("action", action)

    event = DealEvent(
        deal_id=deal.id,
        actor_id=actor_id,
        event_type="transition",
        from_state=from_state,
        to_state=deal.state,
        payload=event_payload or None,
    )
    db.add(event)
    db.add(deal)
    return deal
