from __future__ import annotations

import hashlib
import hmac
import json
import time
from decimal import Decimal
from urllib.parse import urlencode

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, select

from app.api.deps import get_db, get_settings_dep
from app.main import app
from app.models.campaign_application import CampaignApplication
from app.models.channel import Channel
from app.models.deal import Deal, DealSourceType, DealState
from app.models.deal_event import DealEvent
from app.models.deal_escrow import DealEscrow
from app.models.escrow_event import EscrowEvent
from app.models.listing import Listing
from app.models.listing_format import ListingFormat
from app.models.user import User
from app.settings import Settings
from shared.db.base import SQLModel
import shared.telegram.bot_api as bot_api

BOT_TOKEN = "test-bot-token"
_CHANNEL_SEQ = 0


def build_init_data(payload: dict[str, str], bot_token: str = BOT_TOKEN) -> str:
    data = {key: str(value) for key, value in payload.items()}
    data_check_string = "\n".join(f"{key}={data[key]}" for key in sorted(data))
    secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    data["hash"] = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    return urlencode(data)


@pytest.fixture
def db_engine():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    yield engine
    SQLModel.metadata.drop_all(engine)


@pytest.fixture
def client(db_engine):
    def override_get_db():
        with Session(db_engine) as session:
            yield session

    def override_get_settings() -> Settings:
        return Settings(
            _env_file=None,
            TELEGRAM_BOT_TOKEN=BOT_TOKEN,
            TELEGRAM_MEDIA_CHANNEL_ID=123,
        )

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_settings_dep] = override_get_settings
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def _user_payload(user_id: int) -> str:
    return json.dumps({"id": user_id, "first_name": "Ada", "last_name": "Lovelace", "username": "ada"})


def _auth_headers(user_id: int) -> dict[str, str]:
    auth_date = str(int(time.time()))
    init_data = build_init_data({"auth_date": auth_date, "user": _user_payload(user_id)})
    return {"X-Telegram-Init-Data": init_data}


def _create_channel(client: TestClient, owner_id: int, username: str = "@channel") -> int:
    response = client.post(
        "/channels",
        json={"username": username},
        headers=_auth_headers(owner_id),
    )
    assert response.status_code == 201
    return response.json()["id"]


def _create_listing(client: TestClient, channel_id: int, owner_id: int) -> int:
    response = client.post(
        "/listings",
        json={"channel_id": channel_id},
        headers=_auth_headers(owner_id),
    )
    assert response.status_code == 201
    return response.json()["id"]


def _create_listing_format(client: TestClient, listing_id: int, owner_id: int) -> int:
    response = client.post(
        f"/listings/{listing_id}/formats",
        json={
            "placement_type": "post",
            "exclusive_hours": 1,
            "retention_hours": 24,
            "price": "10.00",
        },
        headers=_auth_headers(owner_id),
    )
    assert response.status_code == 201
    return response.json()["id"]


def _create_campaign(client: TestClient, advertiser_id: int) -> int:
    response = client.post(
        "/campaigns",
        json={"title": "Launch", "brief": "Details"},
        headers=_auth_headers(advertiser_id),
    )
    assert response.status_code == 201
    return response.json()["id"]


def _mark_channel_verified(db_engine, channel_id: int) -> None:
    with Session(db_engine) as session:
        channel = session.exec(select(Channel).where(Channel.id == channel_id)).one()
        channel.is_verified = True
        session.add(channel)
        session.commit()


def _create_listing_deal(client: TestClient, advertiser_id: int, owner_id: int) -> int:
    global _CHANNEL_SEQ
    _CHANNEL_SEQ += 1
    channel_id = _create_channel(client, owner_id=owner_id, username=f"@chan{owner_id}_{_CHANNEL_SEQ}")
    listing_id = _create_listing(client, channel_id=channel_id, owner_id=owner_id)
    format_id = _create_listing_format(client, listing_id=listing_id, owner_id=owner_id)
    activate_response = client.put(
        f"/listings/{listing_id}",
        json={"is_active": True},
        headers=_auth_headers(owner_id),
    )
    assert activate_response.status_code == 200

    response = client.post(
        f"/listings/{listing_id}/deals",
        json={
            "listing_format_id": format_id,
            "creative_text": "Hello",
            "creative_media_type": "image",
            "creative_media_ref": "ref",
            "posting_params": {"hour": 10},
        },
        headers=_auth_headers(advertiser_id),
    )
    assert response.status_code == 201
    return response.json()["id"]


def test_create_deal_from_listing(client: TestClient, db_engine) -> None:
    deal_id = _create_listing_deal(client, advertiser_id=101, owner_id=202)

    with Session(db_engine) as session:
        deal = session.exec(select(Deal).where(Deal.id == deal_id)).one()
        assert deal.source_type == DealSourceType.LISTING.value
        assert deal.state == DealState.DRAFT.value
        assert deal.price_ton == Decimal("10.00")
        assert deal.ad_type == "post"
        assert deal.placement_type == "post"
        assert deal.exclusive_hours == 1
        assert deal.retention_hours == 24
        assert deal.verification_window_hours == 24

        event = session.exec(select(DealEvent).where(DealEvent.deal_id == deal_id)).one()
        assert event.event_type == "proposal"


def test_listing_deal_update_moves_to_negotiation(client: TestClient, db_engine) -> None:
    deal_id = _create_listing_deal(client, advertiser_id=101, owner_id=202)

    response = client.patch(
        f"/deals/{deal_id}",
        json={"creative_text": "Updated"},
        headers=_auth_headers(202),
    )
    assert response.status_code == 200
    assert response.json()["state"] == DealState.NEGOTIATION.value


def test_listing_deal_price_locked(client: TestClient) -> None:
    deal_id = _create_listing_deal(client, advertiser_id=101, owner_id=202)

    response = client.patch(
        f"/deals/{deal_id}",
        json={"price_ton": "12.00"},
        headers=_auth_headers(101),
    )
    assert response.status_code == 403


def test_listing_deal_placement_terms_locked(client: TestClient) -> None:
    deal_id = _create_listing_deal(client, advertiser_id=101, owner_id=202)

    response = client.patch(
        f"/deals/{deal_id}",
        json={"placement_type": "story", "exclusive_hours": 6, "retention_hours": 48},
        headers=_auth_headers(101),
    )
    assert response.status_code == 403


def test_accept_deal_requires_counterparty(client: TestClient) -> None:
    deal_id = _create_listing_deal(client, advertiser_id=101, owner_id=202)

    response = client.post(f"/deals/{deal_id}/accept", headers=_auth_headers(101))
    assert response.status_code == 409

    response = client.post(f"/deals/{deal_id}/accept", headers=_auth_headers(202))
    assert response.status_code == 200
    assert response.json()["state"] == DealState.ACCEPTED.value


def test_accept_campaign_application_creates_deal(client: TestClient, db_engine) -> None:
    campaign_id = _create_campaign(client, advertiser_id=101)
    channel_id = _create_channel(client, owner_id=202, username="@ownerchannel")
    _mark_channel_verified(db_engine, channel_id)

    response = client.post(
        f"/campaigns/{campaign_id}/apply",
        json={"channel_id": channel_id, "proposed_format_label": "Post"},
        headers=_auth_headers(202),
    )
    assert response.status_code == 201
    application_id = response.json()["id"]

    response = client.post(
        f"/campaigns/{campaign_id}/applications/{application_id}/accept",
        json={
            "price_ton": "15.00",
            "ad_type": "Post",
            "creative_text": "Campaign",
            "creative_media_type": "video",
            "creative_media_ref": "video-ref",
            "posting_params": {"hour": 12},
        },
        headers=_auth_headers(101),
    )
    assert response.status_code == 201
    payload = response.json()
    assert payload["source_type"] == DealSourceType.CAMPAIGN.value
    assert payload["state"] == DealState.DRAFT.value

    with Session(db_engine) as session:
        application = session.exec(select(CampaignApplication).where(CampaignApplication.id == application_id)).one()
        assert application.status == "accepted"


def test_send_deal_message(client: TestClient, monkeypatch) -> None:
    def fake_post(url: str, json: dict):
        class DummyResponse:
            status_code = 200

            def json(self) -> dict:
                return {"ok": True, "result": {"message_id": 1}}

        return DummyResponse()

    monkeypatch.setattr(bot_api.httpx, "post", fake_post)

    deal_id = _create_listing_deal(client, advertiser_id=101, owner_id=202)

    response = client.post(
        f"/deals/{deal_id}/messages",
        json={"text": "Hello"},
        headers=_auth_headers(101),
    )
    assert response.status_code == 201
    payload = response.json()
    assert payload["deal_id"] == deal_id
    assert payload["text"] == "Hello"


def test_deals_inbox_filters_and_pagination(client: TestClient, db_engine) -> None:
    deal_id_one = _create_listing_deal(client, advertiser_id=101, owner_id=202)
    deal_id_two = _create_listing_deal(client, advertiser_id=101, owner_id=202)

    with Session(db_engine) as session:
        deal_one = session.exec(select(Deal).where(Deal.id == deal_id_one)).one()
        deal_two = session.exec(select(Deal).where(Deal.id == deal_id_two)).one()
        deal_one.state = DealState.CREATIVE_SUBMITTED.value
        deal_two.state = DealState.ACCEPTED.value
        session.add(deal_one)
        session.add(deal_two)
        session.commit()

    response = client.get("/deals?role=owner&state=CREATIVE_SUBMITTED&page=1&page_size=20", headers=_auth_headers(202))
    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    assert payload["items"][0]["id"] == deal_id_one

    response = client.get("/deals?role=owner&page=1&page_size=1", headers=_auth_headers(202))
    assert response.status_code == 200
    payload = response.json()
    assert payload["page_size"] == 1
    assert len(payload["items"]) == 1


def test_deal_detail_participant_fields(client: TestClient, db_engine) -> None:
    deal_id = _create_listing_deal(client, advertiser_id=101, owner_id=202)

    with Session(db_engine) as session:
        deal = session.exec(select(Deal).where(Deal.id == deal_id)).one()
        channel = session.exec(select(Channel).where(Channel.id == deal.channel_id)).one()
        channel.title = "Channel Title"
        session.add(channel)
        advertiser = session.exec(select(User).where(User.id == deal.advertiser_id)).one()
        advertiser.first_name = "Ada"
        advertiser.last_name = "Lovelace"
        session.add(advertiser)
        session.commit()

    response = client.get(f"/deals/{deal_id}", headers=_auth_headers(101))
    assert response.status_code == 200
    payload = response.json()
    assert payload["channel_title"] == "Channel Title"
    assert payload["advertiser_first_name"] == "Ada"
    assert payload["advertiser_last_name"] == "Lovelace"

    response = client.get(f"/deals/{deal_id}", headers=_auth_headers(999))
    assert response.status_code == 403


def test_deal_timeline_merges_events(client: TestClient, db_engine) -> None:
    deal_id = _create_listing_deal(client, advertiser_id=101, owner_id=202)
    with Session(db_engine) as session:
        deal = session.exec(select(Deal).where(Deal.id == deal_id)).one()
        escrow = DealEscrow(
            deal_id=deal.id,
            state="CREATED",
            expected_amount_ton=deal.price_ton,
            received_amount_ton=Decimal("0"),
            fee_percent=Decimal("1.00"),
        )
        session.add(escrow)
        session.flush()

        session.add(
            DealEvent(
                deal_id=deal.id,
                actor_id=deal.advertiser_id,
                event_type="transition",
                from_state="DRAFT",
                to_state="NEGOTIATION",
            )
        )
        session.add(
            EscrowEvent(
                escrow_id=escrow.id,
                actor_user_id=None,
                from_state=None,
                to_state="CREATED",
                event_type="created",
                payload=None,
            )
        )
        session.commit()

    response = client.get(f"/deals/{deal_id}/events?limit=1", headers=_auth_headers(101))
    assert response.status_code == 200
    payload = response.json()
    assert len(payload["items"]) == 1
    assert payload["next_cursor"] is not None

    response_page_two = client.get(
        f"/deals/{deal_id}/events",
        headers=_auth_headers(101),
        params={"cursor": payload["next_cursor"], "limit": 1},
    )
    assert response_page_two.status_code == 200
    payload_two = response_page_two.json()
    assert len(payload_two["items"]) == 1


def test_creative_endpoints_flow(client: TestClient, db_engine) -> None:
    deal_id = _create_listing_deal(client, advertiser_id=101, owner_id=202)
    client.post(f"/deals/{deal_id}/accept", headers=_auth_headers(202))

    response = client.post(
        f"/deals/{deal_id}/creative/submit",
        json={
            "creative_text": "New creative",
            "creative_media_type": "image",
            "creative_media_ref": "file-id",
        },
        headers=_auth_headers(202),
    )
    assert response.status_code == 200
    assert response.json()["state"] == DealState.CREATIVE_SUBMITTED.value

    response = client.post(f"/deals/{deal_id}/creative/request-edits", headers=_auth_headers(101))
    assert response.status_code == 200
    assert response.json()["state"] == DealState.CREATIVE_CHANGES_REQUESTED.value

    response = client.post(
        f"/deals/{deal_id}/creative/submit",
        json={
            "creative_text": "Updated creative",
            "creative_media_type": "image",
            "creative_media_ref": "file-id-2",
        },
        headers=_auth_headers(202),
    )
    assert response.status_code == 200
    assert response.json()["state"] == DealState.CREATIVE_SUBMITTED.value

    response = client.post(f"/deals/{deal_id}/creative/approve", headers=_auth_headers(101))
    assert response.status_code == 200
    assert response.json()["state"] == DealState.CREATIVE_APPROVED.value


def test_creative_upload_endpoint(client: TestClient, monkeypatch) -> None:
    def fake_post(url: str, data: dict, files: dict):
        class DummyResponse:
            status_code = 200

            def json(self) -> dict:
                return {"ok": True, "result": {"photo": [{"file_id": "file-1"}]}}

        return DummyResponse()

    monkeypatch.setattr(bot_api.httpx, "post", fake_post)

    deal_id = _create_listing_deal(client, advertiser_id=101, owner_id=202)
    client.post(f"/deals/{deal_id}/accept", headers=_auth_headers(202))

    response = client.post(
        f"/deals/{deal_id}/creative/upload",
        files={"file": ("photo.jpg", b"data", "image/jpeg")},
        headers=_auth_headers(202),
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["creative_media_ref"] == "file-1"
    assert payload["creative_media_type"] == "image"
