from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from sqlalchemy import func, or_
from sqlmodel import Session, select

from app.api.deps import get_current_user, get_db, get_settings_dep
from app.domain.escrow_fsm import EscrowState, EscrowTransitionError, apply_escrow_transition
from app.models.channel import Channel
from app.models.deal import Deal, DealSourceType, DealState
from app.models.deal_escrow import DealEscrow
from app.models.deal_event import DealEvent
from app.models.escrow_event import EscrowEvent
from app.models.user import User
from app.schemas.escrow import EscrowInitResponse, EscrowStatusResponse, TonConnectTxResponse
from app.schemas.deals import (
    DealCreativeSubmit,
    DealCreativeUploadResponse,
    DealDetail,
    DealInboxItem,
    DealInboxPage,
    DealMessageCreate,
    DealMessageSummary,
    DealSummary,
    DealTimelineEvent,
    DealTimelinePage,
    DealUpdate,
)
from app.services.deal_fsm import DealAction, DealActorRole, DealTransitionError, apply_transition
from app.services.ton.errors import TonConfigError
from app.services.ton.tonconnect import build_tonconnect_transaction
from app.services.ton.wallets import generate_deal_deposit_address
from app.settings import Settings
from shared.telegram.bot_api import BotApiService
from shared.telegram.errors import TelegramApiError, TelegramConfigError

router = APIRouter(prefix="/deals", tags=["deals"])

ALLOWED_MEDIA_TYPES = {"image", "video"}
DEFAULT_PAGE = 1
DEFAULT_PAGE_SIZE = 20
DEFAULT_TIMELINE_LIMIT = 20
CURSOR_SOURCE_ORDER = {"deal": 0, "escrow": 1}


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
        scheduled_at=deal.scheduled_at,
        verification_window_hours=deal.verification_window_hours,
        posted_at=deal.posted_at,
        posted_message_id=deal.posted_message_id,
        posted_content_hash=deal.posted_content_hash,
        verified_at=deal.verified_at,
        state=deal.state,
        created_at=deal.created_at,
        updated_at=deal.updated_at,
    )


def _load_deal(db: Session, deal_id: int) -> Deal:
    deal = db.exec(select(Deal).where(Deal.id == deal_id)).first()
    if deal is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deal not found")
    return deal


def _load_escrow(db: Session, deal_id: int) -> DealEscrow | None:
    return db.exec(select(DealEscrow).where(DealEscrow.deal_id == deal_id)).first()


def _require_actor_role(deal: Deal, user_id: int | None) -> str:
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    if user_id == deal.advertiser_id:
        return DealActorRole.advertiser.value
    if user_id == deal.channel_owner_id:
        return DealActorRole.channel_owner.value
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")


def _require_advertiser(deal: Deal, user_id: int | None) -> None:
    if user_id is None or user_id != deal.advertiser_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only advertiser may perform this action")


def _require_non_empty(value: str | None, *, field: str) -> str:
    if value is None or not value.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid {field}")
    return value.strip()


def _require_media_type(value: str | None) -> str:
    normalized = _require_non_empty(value, field="creative_media_type")
    if normalized not in ALLOWED_MEDIA_TYPES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid creative_media_type")
    return normalized


def _parse_int(value: str | None, *, field: str, minimum: int | None = None) -> int | None:
    if value is None:
        return None
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid {field}")
    if minimum is not None and parsed < minimum:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid {field}")
    return parsed


def _encode_cursor(created_at: datetime, source: str, event_id: int) -> str:
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)
    return f"{created_at.isoformat()}|{source}|{event_id}"


def _decode_cursor(raw: str) -> tuple[datetime, int, int]:
    parts = raw.split("|")
    if len(parts) != 3:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid cursor")
    raw_ts, source, raw_id = parts
    try:
        timestamp = datetime.fromisoformat(raw_ts)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid cursor") from exc
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)
    source_key = CURSOR_SOURCE_ORDER.get(source)
    if source_key is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid cursor")
    try:
        event_id = int(raw_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid cursor") from exc
    return timestamp, source_key, event_id


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


@router.get("", response_model=DealInboxPage)
def list_deals(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DealInboxPage:
    params = request.query_params
    role = params.get("role")
    state = params.get("state")

    page = _parse_int(params.get("page"), field="page", minimum=1) or DEFAULT_PAGE
    page_size = _parse_int(params.get("page_size"), field="page_size", minimum=1) or DEFAULT_PAGE_SIZE

    if role not in {None, "owner", "advertiser"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid role")

    if current_user.id is None:
        return DealInboxPage(page=page, page_size=page_size, total=0, items=[])

    stmt = (
        select(Deal, Channel.username, Channel.title)
        .join(Channel, Channel.id == Deal.channel_id)
        .order_by(Deal.updated_at.desc(), Deal.id.desc())
    )

    if role == "owner":
        stmt = stmt.where(Deal.channel_owner_id == current_user.id)
    elif role == "advertiser":
        stmt = stmt.where(Deal.advertiser_id == current_user.id)
    else:
        stmt = stmt.where(
            or_(
                Deal.advertiser_id == current_user.id,
                Deal.channel_owner_id == current_user.id,
            )
        )

    if state:
        stmt = stmt.where(Deal.state == state)

    total_stmt = select(func.count()).select_from(stmt.subquery())
    total_result = db.exec(total_stmt).one()
    total = total_result if isinstance(total_result, int) else total_result[0]

    offset = (page - 1) * page_size
    rows = db.exec(stmt.limit(page_size).offset(offset)).all()

    items = [
        DealInboxItem(
            id=deal.id,
            state=deal.state,
            channel_id=deal.channel_id,
            channel_username=channel_username,
            channel_title=channel_title,
            advertiser_id=deal.advertiser_id,
            price_ton=deal.price_ton,
            ad_type=deal.ad_type,
            updated_at=deal.updated_at,
        )
        for deal, channel_username, channel_title in rows
    ]

    return DealInboxPage(page=page, page_size=page_size, total=total, items=items)


@router.get("/{deal_id}", response_model=DealDetail)
def read_deal(
    deal_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DealDetail:
    deal = _load_deal(db, deal_id)
    _require_actor_role(deal, current_user.id)

    channel = db.exec(select(Channel).where(Channel.id == deal.channel_id)).first()
    advertiser = db.exec(select(User).where(User.id == deal.advertiser_id)).first()

    return DealDetail(
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
        scheduled_at=deal.scheduled_at,
        verification_window_hours=deal.verification_window_hours,
        posted_at=deal.posted_at,
        posted_message_id=deal.posted_message_id,
        posted_content_hash=deal.posted_content_hash,
        verified_at=deal.verified_at,
        state=deal.state,
        created_at=deal.created_at,
        updated_at=deal.updated_at,
        channel_username=channel.username if channel else None,
        channel_title=channel.title if channel else None,
        advertiser_username=advertiser.username if advertiser else None,
        advertiser_first_name=advertiser.first_name if advertiser else None,
        advertiser_last_name=advertiser.last_name if advertiser else None,
    )


@router.get("/{deal_id}/events", response_model=DealTimelinePage)
def list_deal_events(
    deal_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DealTimelinePage:
    deal = _load_deal(db, deal_id)
    _require_actor_role(deal, current_user.id)

    params = request.query_params
    limit = _parse_int(params.get("limit"), field="limit", minimum=1) or DEFAULT_TIMELINE_LIMIT
    cursor_raw = params.get("cursor")
    cursor_key = _decode_cursor(cursor_raw) if cursor_raw else None

    deal_events = db.exec(select(DealEvent).where(DealEvent.deal_id == deal.id)).all()
    escrow_events: list[EscrowEvent] = []
    escrow = _load_escrow(db, deal.id)
    if escrow is not None:
        escrow_events = db.exec(select(EscrowEvent).where(EscrowEvent.escrow_id == escrow.id)).all()

    merged: list[dict] = []
    for event in deal_events:
        created_at = event.created_at
        if created_at is not None and created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)
        merged.append(
            {
                "source": "deal",
                "id": event.id,
                "created_at": created_at,
                "event_type": event.event_type,
                "from_state": event.from_state,
                "to_state": event.to_state,
                "payload": event.payload,
                "actor_id": event.actor_id,
            }
        )
    for event in escrow_events:
        created_at = event.created_at
        if created_at is not None and created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)
        merged.append(
            {
                "source": "escrow",
                "id": event.id,
                "created_at": created_at,
                "event_type": event.event_type,
                "from_state": event.from_state,
                "to_state": event.to_state,
                "payload": event.payload,
                "actor_id": event.actor_user_id,
            }
        )

    merged.sort(
        key=lambda item: (
            item["created_at"],
            CURSOR_SOURCE_ORDER[item["source"]],
            item["id"],
        )
    )

    if cursor_key is not None:
        merged = [
            item
            for item in merged
            if (item["created_at"], CURSOR_SOURCE_ORDER[item["source"]], item["id"]) > cursor_key
        ]

    next_cursor = None
    if len(merged) > limit:
        last_item = merged[limit - 1]
        next_cursor = _encode_cursor(last_item["created_at"], last_item["source"], last_item["id"])
        merged = merged[:limit]

    items = [
        DealTimelineEvent(
            event_type=item["event_type"],
            from_state=item["from_state"],
            to_state=item["to_state"],
            payload=item["payload"],
            created_at=item["created_at"],
            actor_id=item["actor_id"],
        )
        for item in merged
    ]

    return DealTimelinePage(items=items, next_cursor=next_cursor)


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


@router.post("/{deal_id}/creative/submit", response_model=DealSummary)
def submit_creative(
    deal_id: int,
    payload: DealCreativeSubmit,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DealSummary:
    deal = _load_deal(db, deal_id)
    actor_role = _require_actor_role(deal, current_user.id)
    if actor_role != DealActorRole.channel_owner.value:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only channel owner may submit creative")

    if deal.state not in {DealState.ACCEPTED.value, DealState.CREATIVE_CHANGES_REQUESTED.value}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Deal cannot accept creative")

    deal.creative_text = _require_non_empty(payload.creative_text, field="creative_text")
    deal.creative_media_type = _require_media_type(payload.creative_media_type)
    deal.creative_media_ref = _require_non_empty(payload.creative_media_ref, field="creative_media_ref")

    try:
        apply_transition(
            db,
            deal=deal,
            action=DealAction.creative_submit.value,
            actor_id=current_user.id,
            actor_role=actor_role,
            payload={"reason": "creative_submitted"},
        )
    except DealTransitionError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    db.commit()
    db.refresh(deal)
    return _deal_summary(deal)


@router.post("/{deal_id}/creative/approve", response_model=DealSummary)
def approve_creative(
    deal_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DealSummary:
    deal = _load_deal(db, deal_id)
    actor_role = _require_actor_role(deal, current_user.id)
    if actor_role != DealActorRole.advertiser.value:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only advertiser may approve creative")

    if deal.state != DealState.CREATIVE_SUBMITTED.value:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Deal is not awaiting approval")

    try:
        apply_transition(
            db,
            deal=deal,
            action=DealAction.creative_approve.value,
            actor_id=current_user.id,
            actor_role=actor_role,
            payload={"reason": "creative_approved"},
        )
    except DealTransitionError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    db.commit()
    db.refresh(deal)
    return _deal_summary(deal)


@router.post("/{deal_id}/creative/request-edits", response_model=DealSummary)
def request_creative_edits(
    deal_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DealSummary:
    deal = _load_deal(db, deal_id)
    actor_role = _require_actor_role(deal, current_user.id)
    if actor_role != DealActorRole.advertiser.value:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only advertiser may request edits")

    if deal.state != DealState.CREATIVE_SUBMITTED.value:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Deal is not awaiting approval")

    try:
        apply_transition(
            db,
            deal=deal,
            action=DealAction.creative_request_edits.value,
            actor_id=current_user.id,
            actor_role=actor_role,
            payload={"reason": "creative_changes_requested"},
        )
    except DealTransitionError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    db.commit()
    db.refresh(deal)
    return _deal_summary(deal)


@router.post("/{deal_id}/creative/upload", response_model=DealCreativeUploadResponse)
def upload_creative_media(
    deal_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    settings: Settings = Depends(get_settings_dep),
) -> DealCreativeUploadResponse:
    deal = _load_deal(db, deal_id)
    actor_role = _require_actor_role(deal, current_user.id)
    if actor_role != DealActorRole.channel_owner.value:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only channel owner may upload creative")

    content_type = file.content_type or ""
    if content_type.startswith("image/"):
        media_type = "image"
    elif content_type.startswith("video/"):
        media_type = "video"
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid creative_media_type")

    content = file.file.read()
    if not content:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Empty upload")

    service = BotApiService(settings)
    try:
        result = service.upload_media(
            media_type=media_type,
            filename=file.filename or f"creative.{media_type}",
            content=content,
        )
    except (TelegramApiError, TelegramConfigError) as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Failed to upload media") from exc

    return DealCreativeUploadResponse(
        creative_media_ref=result["file_id"],
        creative_media_type=result["media_type"],
    )


@router.post("/{deal_id}/escrow/init", response_model=EscrowInitResponse)
def init_escrow(
    deal_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    settings: Settings = Depends(get_settings_dep),
) -> EscrowInitResponse:
    deal = _load_deal(db, deal_id)
    _require_advertiser(deal, current_user.id)

    if deal.state != DealState.CREATIVE_APPROVED.value:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Deal is not creative-approved")

    if deal.price_ton <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid deal price")

    if settings.TON_FEE_PERCENT is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="TON_FEE_PERCENT is not configured")

    escrow = _load_escrow(db, deal.id)
    if escrow is None:
        escrow = DealEscrow(
            deal_id=deal.id,
            state=EscrowState.CREATED.value,
            expected_amount_ton=deal.price_ton,
            received_amount_ton=Decimal("0"),
            fee_percent=settings.TON_FEE_PERCENT,
        )
        db.add(escrow)
        db.flush()

    if escrow.state == EscrowState.FAILED.value:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Escrow is in failed state")

    if not escrow.deposit_address:
        try:
            escrow.deposit_address = generate_deal_deposit_address(deal_id=deal.id, settings=settings)
        except TonConfigError as exc:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
        db.add(escrow)

    if escrow.state == EscrowState.CREATED.value:
        try:
            apply_escrow_transition(
                db,
                escrow=escrow,
                to_state=EscrowState.AWAITING_DEPOSIT.value,
                actor_user_id=current_user.id,
                event_type="address_generated",
                payload={"deposit_address": escrow.deposit_address},
            )
        except EscrowTransitionError as exc:
            db.rollback()
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    db.commit()
    db.refresh(escrow)

    if not escrow.deposit_address:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Deposit address is missing")

    return EscrowInitResponse(
        escrow_id=escrow.id,
        deal_id=deal.id,
        state=escrow.state,
        deposit_address=escrow.deposit_address,
        fee_percent=escrow.fee_percent,
        confirmations_required=settings.TON_CONFIRMATIONS_REQUIRED,
    )


@router.post("/{deal_id}/escrow/tonconnect-tx", response_model=TonConnectTxResponse)
def tonconnect_tx(
    deal_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    settings: Settings = Depends(get_settings_dep),
) -> TonConnectTxResponse:
    deal = _load_deal(db, deal_id)
    _require_advertiser(deal, current_user.id)

    if deal.state != DealState.CREATIVE_APPROVED.value:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Deal is not creative-approved")

    escrow = _load_escrow(db, deal.id)
    if escrow is None or not escrow.deposit_address:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Escrow is not initialized")

    try:
        payload = build_tonconnect_transaction(
            deposit_address=escrow.deposit_address,
            amount_ton=deal.price_ton,
            settings=settings,
        )
    except TonConfigError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc

    return TonConnectTxResponse(escrow_id=escrow.id, deal_id=deal.id, payload=payload)


@router.get("/{deal_id}/escrow", response_model=EscrowStatusResponse)
def get_escrow_status(
    deal_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> EscrowStatusResponse:
    deal = _load_deal(db, deal_id)
    _require_actor_role(deal, current_user.id)

    escrow = _load_escrow(db, deal.id)
    if escrow is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Escrow not found")

    return EscrowStatusResponse(
        state=escrow.state,
        deposit_address=escrow.deposit_address,
        expected_amount_ton=escrow.expected_amount_ton,
        received_amount_ton=escrow.received_amount_ton,
        deposit_confirmations=escrow.deposit_confirmations,
    )


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
