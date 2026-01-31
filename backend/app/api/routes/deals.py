from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.api.deps import get_current_user, get_db, get_settings_dep
from app.models.deal import Deal, DealSourceType, DealState
from app.models.deal_event import DealEvent
from app.models.user import User
from app.schemas.deals import DealMessageCreate, DealMessageSummary, DealSummary, DealUpdate
from app.services.deal_fsm import DealAction, DealActorRole, DealTransitionError, apply_transition
from app.settings import Settings
from shared.telegram.bot_api import BotApiService
from shared.telegram.errors import TelegramApiError, TelegramConfigError

router = APIRouter(prefix="/deals", tags=["deals"])

ALLOWED_MEDIA_TYPES = {"image", "video"}


def _deal_summary(deal: Deal) -> DealSummary:
    return DealSummary(
        id=deal.id,
        source_type=deal.source_type,
        advertiser_id=deal.advertiser_id,
        channel_id=deal.channel_id,
        channel_owner_id=deal.channel_owner_id,
        listing_id=deal.listing_id,
        listing_format_id=deal.listing_format_id,
        campaign_id=deal.campaign_id,
        campaign_application_id=deal.campaign_application_id,
        price_ton=deal.price_ton,
        ad_type=deal.ad_type,
        creative_text=deal.creative_text,
        creative_media_type=deal.creative_media_type,
        creative_media_ref=deal.creative_media_ref,
        posting_params=deal.posting_params,
        state=deal.state,
        created_at=deal.created_at,
        updated_at=deal.updated_at,
    )


def _load_deal(db: Session, deal_id: int) -> Deal:
    deal = db.exec(select(Deal).where(Deal.id == deal_id)).first()
    if deal is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deal not found")
    return deal


def _require_actor_role(deal: Deal, user_id: int | None) -> str:
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    if user_id == deal.advertiser_id:
        return DealActorRole.advertiser.value
    if user_id == deal.channel_owner_id:
        return DealActorRole.channel_owner.value
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")


def _require_non_empty(value: str | None, *, field: str) -> str:
    if value is None or not value.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid {field}")
    return value.strip()


def _require_media_type(value: str | None) -> str:
    normalized = _require_non_empty(value, field="creative_media_type")
    if normalized not in ALLOWED_MEDIA_TYPES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid creative_media_type")
    return normalized


def _validate_price(value: Decimal | None) -> Decimal | None:
    if value is None:
        return None
    try:
        normalized = Decimal(value)
    except (InvalidOperation, TypeError):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid price_ton")
    if normalized < 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid price_ton")
    return normalized


def _serialize_payload(payload: dict) -> dict:
    serialized: dict[str, object] = {}
    for key, value in payload.items():
        if isinstance(value, Decimal):
            serialized[key] = str(value)
        else:
            serialized[key] = value
    return serialized


def _latest_proposal_actor(db: Session, deal_id: int) -> int | None:
    event = (
        db.exec(
            select(DealEvent)
            .where(DealEvent.deal_id == deal_id)
            .where(DealEvent.event_type == "proposal")
            .order_by(DealEvent.created_at.desc(), DealEvent.id.desc())
        )
        .first()
    )
    return event.actor_id if event else None


@router.patch("/{deal_id}", response_model=DealSummary)
def update_deal(
    deal_id: int,
    payload: DealUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DealSummary:
    deal = _load_deal(db, deal_id)
    actor_role = _require_actor_role(deal, current_user.id)

    if deal.state not in {DealState.DRAFT.value, DealState.NEGOTIATION.value}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Deal cannot be updated")

    updates: dict[str, object] = {}

    if payload.price_ton is not None:
        updates["price_ton"] = _validate_price(payload.price_ton)
    if payload.ad_type is not None:
        updates["ad_type"] = _require_non_empty(payload.ad_type, field="ad_type")
    if payload.creative_text is not None:
        updates["creative_text"] = _require_non_empty(payload.creative_text, field="creative_text")
    if payload.creative_media_type is not None:
        updates["creative_media_type"] = _require_media_type(payload.creative_media_type)
    if payload.creative_media_ref is not None:
        updates["creative_media_ref"] = _require_non_empty(payload.creative_media_ref, field="creative_media_ref")
    if payload.posting_params is not None:
        updates["posting_params"] = payload.posting_params

    if not updates:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fields to update")

    if deal.source_type == DealSourceType.LISTING.value:
        if "price_ton" in updates or "ad_type" in updates:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Price and ad type are locked")
    elif deal.source_type == DealSourceType.CAMPAIGN.value:
        if actor_role == DealActorRole.channel_owner.value:
            forbidden = {"price_ton", "ad_type"}
            if forbidden.intersection(updates.keys()):
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only advertiser can edit price or ad type")

    for field, value in updates.items():
        setattr(deal, field, value)

    deal.updated_at = datetime.now(timezone.utc)
    db.add(deal)

    proposal_event = DealEvent(
        deal_id=deal.id,
        actor_id=current_user.id,
        event_type="proposal",
        payload=_serialize_payload(updates),
    )
    db.add(proposal_event)

    if deal.state == DealState.DRAFT.value:
        try:
            apply_transition(
                db,
                deal=deal,
                action=DealAction.propose.value,
                actor_id=current_user.id,
                actor_role=actor_role,
                payload={"reason": "proposal"},
            )
        except DealTransitionError as exc:
            db.rollback()
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    db.commit()
    db.refresh(deal)
    return _deal_summary(deal)


@router.post("/{deal_id}/accept", response_model=DealSummary)
def accept_deal(
    deal_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DealSummary:
    deal = _load_deal(db, deal_id)
    actor_role = _require_actor_role(deal, current_user.id)

    if deal.state not in {DealState.DRAFT.value, DealState.NEGOTIATION.value}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Deal cannot be accepted")

    last_actor_id = _latest_proposal_actor(db, deal.id)
    if last_actor_id is None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="No proposal to accept")
    if last_actor_id == current_user.id:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Cannot accept your own proposal")

    try:
        if deal.state == DealState.DRAFT.value:
            apply_transition(
                db,
                deal=deal,
                action=DealAction.advance.value,
                actor_id=None,
                actor_role=DealActorRole.system.value,
                payload={"reason": "accept_from_draft"},
            )
        apply_transition(
            db,
            deal=deal,
            action=DealAction.accept.value,
            actor_id=current_user.id,
            actor_role=actor_role,
            payload={"reason": "accepted"},
        )
    except DealTransitionError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    db.commit()
    db.refresh(deal)
    return _deal_summary(deal)


@router.post("/{deal_id}/messages", response_model=DealMessageSummary, status_code=status.HTTP_201_CREATED)
def send_deal_message(
    deal_id: int,
    payload: DealMessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    settings: Settings = Depends(get_settings_dep),
) -> DealMessageSummary:
    deal = _load_deal(db, deal_id)
    sender_role = _require_actor_role(deal, current_user.id)

    message_text = _require_non_empty(payload.text, field="text")

    recipient_id = deal.channel_owner_id if sender_role == DealActorRole.advertiser.value else deal.advertiser_id
    recipient = db.exec(select(User).where(User.id == recipient_id)).first()
    if recipient is None or recipient.telegram_user_id is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipient not found")

    event = DealEvent(
        deal_id=deal.id,
        actor_id=current_user.id,
        event_type="message",
        payload={"text": message_text, "to_user_id": recipient.id},
    )
    db.add(event)
    db.commit()
    db.refresh(event)

    service = BotApiService(settings)
    try:
        service.send_message(chat_id=recipient.telegram_user_id, text=message_text)
    except (TelegramApiError, TelegramConfigError) as exc:
        event.payload = {"text": message_text, "to_user_id": recipient.id, "delivery_error": str(exc)}
        db.add(event)
        db.commit()
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Failed to deliver message") from exc

    return DealMessageSummary(
        id=event.id,
        deal_id=event.deal_id,
        actor_id=event.actor_id,
        text=message_text,
        created_at=event.created_at,
    )
