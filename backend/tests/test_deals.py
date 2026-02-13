from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
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
from app.models.campaign_request import CampaignRequest
from app.models.channel import Channel
from app.models.deal import Deal, DealSourceType, DealState
from app.models.deal_event import DealEvent
from app.models.deal_escrow import DealEscrow
from app.models.escrow_event import EscrowEvent
from app.models.user import User
from app.settings import Settings
from shared.db.base import SQLModel
import shared.telegram.bot_api as bot_api

BOT_TOKEN = "test-bot-token"
_CHANNEL_SEQ = 0


@pytest.fixture(autouse=True)
def stub_telegram_http(monkeypatch) -> None:
    def fake_post(url: str, **kwargs):
        class DummyResponse:
            status_code = 200
            text = "ok"

            def json(self) -> dict:
                if url.endswith("/sendPhoto"):
                    return {
                        "ok": True,
                        "result": {"photo": [{"file_id": "stub-photo-file"}]},
                    }
                if url.endswith("/sendVideo"):
                    return {
                        "ok": True,
                        "result": {"video": {"file_id": "stub-video-file"}},
                    }
                if url.endswith("/getFile"):
                    return {"ok": True, "result": {"file_path": "stub/path.bin"}}
                return {"ok": True, "result": {"message_id": 1}}

        return DummyResponse()

    def fake_get(url: str, **kwargs):
        class DummyResponse:
            status_code = 200
            content = b"stub-bytes"
            headers = {"content-type": "application/octet-stream"}
            text = "ok"

        return DummyResponse()

    monkeypatch.setattr(bot_api.httpx, "post", fake_post)
    monkeypatch.setattr(bot_api.httpx, "get", fake_get)


def build_init_data(payload: dict[str, str], bot_token: str = BOT_TOKEN) -> str:
    data = {key: str(value) for key, value in payload.items()}
    data_check_string = "\n".join(f"{key}={data[key]}" for key in sorted(data))
    secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    data["hash"] = hmac.new(
        secret_key, data_check_string.encode(), hashlib.sha256
    ).hexdigest()
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
    return json.dumps(
        {"id": user_id, "first_name": "Ada", "last_name": "Lovelace", "username": "ada"}
    )


def _auth_headers(user_id: int) -> dict[str, str]:
    auth_date = str(int(time.time()))
    init_data = build_init_data(
        {"auth_date": auth_date, "user": _user_payload(user_id)}
    )
    return {"X-Telegram-Init-Data": init_data}


def _create_channel(
    client: TestClient, owner_id: int, username: str = "@channel"
) -> int:
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


def _create_campaign(
    client: TestClient,
    advertiser_id: int,
    max_acceptances: int | None = None,
    budget_ton: str | None = None,
) -> int:
    payload: dict[str, object] = {"title": "Launch", "brief": "Details"}
    if max_acceptances is not None:
        payload["max_acceptances"] = max_acceptances
    if budget_ton is not None:
        payload["budget_ton"] = budget_ton
    response = client.post(
        "/campaigns",
        json=payload,
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


def _create_listing_deal(
    client: TestClient,
    advertiser_id: int,
    owner_id: int,
    *,
    start_at: str | None = None,
) -> int:
    global _CHANNEL_SEQ
    _CHANNEL_SEQ += 1
    channel_id = _create_channel(
        client, owner_id=owner_id, username=f"@chan{owner_id}_{_CHANNEL_SEQ}"
    )
    listing_id = _create_listing(client, channel_id=channel_id, owner_id=owner_id)
    format_id = _create_listing_format(client, listing_id=listing_id, owner_id=owner_id)
    activate_response = client.put(
        f"/listings/{listing_id}",
        json={"is_active": True},
        headers=_auth_headers(owner_id),
    )
    assert activate_response.status_code == 200

    payload: dict[str, object] = {
        "listing_format_id": format_id,
        "creative_text": "Hello",
        "creative_media_type": "image",
        "creative_media_ref": "ref",
        "posting_params": {"hour": 10},
    }
    if start_at is not None:
        payload["start_at"] = start_at

    response = client.post(
        f"/listings/{listing_id}/deals",
        json=payload,
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

        event = session.exec(
            select(DealEvent).where(DealEvent.deal_id == deal_id)
        ).one()
        assert event.event_type == "proposal"


def test_create_deal_from_listing_sends_offer_notification(
    client: TestClient, monkeypatch
) -> None:
    calls: list[int] = []
    monkeypatch.setattr(
        "app.api.routes.listings.notify_listing_offer_received",
        lambda **kwargs: calls.append(kwargs["deal"].id),
    )

    deal_id = _create_listing_deal(client, advertiser_id=101, owner_id=202)
    assert calls == [deal_id]


def test_listing_deal_start_at_is_saved_as_scheduled_at(
    client: TestClient, db_engine
) -> None:
    deal_id = _create_listing_deal(
        client,
        advertiser_id=101,
        owner_id=202,
        start_at="2026-02-10T12:30:00+00:00",
    )

    with Session(db_engine) as session:
        deal = session.exec(select(Deal).where(Deal.id == deal_id)).one()
        assert deal.scheduled_at is not None
        assert deal.scheduled_at.isoformat() == "2026-02-10T12:30:00"


def test_listing_deal_update_moves_to_negotiation(
    client: TestClient, db_engine
) -> None:
    deal_id = _create_listing_deal(client, advertiser_id=101, owner_id=202)

    response = client.patch(
        f"/deals/{deal_id}",
        json={"creative_text": "Updated"},
        headers=_auth_headers(202),
    )
    assert response.status_code == 200
    assert response.json()["state"] == DealState.NEGOTIATION.value


def test_listing_deal_start_time_is_negotiable(client: TestClient, db_engine) -> None:
    deal_id = _create_listing_deal(client, advertiser_id=101, owner_id=202)

    response = client.patch(
        f"/deals/{deal_id}",
        json={"start_at": "2026-02-11T09:00:00+00:00"},
        headers=_auth_headers(202),
    )
    assert response.status_code == 200

    with Session(db_engine) as session:
        deal = session.exec(select(Deal).where(Deal.id == deal_id)).one()
        assert deal.scheduled_at is not None
        assert deal.scheduled_at.isoformat() == "2026-02-11T09:00:00"


def test_listing_deal_price_locked(client: TestClient) -> None:
    deal_id = _create_listing_deal(client, advertiser_id=101, owner_id=202)

    response = client.patch(
        f"/deals/{deal_id}",
        json={"price_ton": "12.00"},
        headers=_auth_headers(202),
    )
    assert response.status_code == 403


def test_listing_deal_placement_terms_locked(client: TestClient) -> None:
    deal_id = _create_listing_deal(client, advertiser_id=101, owner_id=202)

    response = client.patch(
        f"/deals/{deal_id}",
        json={"placement_type": "story", "exclusive_hours": 6, "retention_hours": 48},
        headers=_auth_headers(202),
    )
    assert response.status_code == 403


def test_accept_deal_requires_counterparty(client: TestClient, monkeypatch) -> None:
    deal_id = _create_listing_deal(client, advertiser_id=101, owner_id=202)
    calls: list[int] = []
    monkeypatch.setattr(
        "app.api.routes.deals.notify_deal_offer_accepted",
        lambda **kwargs: calls.append(kwargs["deal"].id),
    )

    response = client.post(f"/deals/{deal_id}/accept", headers=_auth_headers(101))
    assert response.status_code == 409

    response = client.post(f"/deals/{deal_id}/accept", headers=_auth_headers(202))
    assert response.status_code == 200
    assert response.json()["state"] == DealState.CREATIVE_APPROVED.value

    assert calls == [deal_id]


def test_reject_deal_requires_counterparty(client: TestClient) -> None:
    deal_id = _create_listing_deal(client, advertiser_id=101, owner_id=202)

    response = client.post(f"/deals/{deal_id}/reject", headers=_auth_headers(101))
    assert response.status_code == 409

    response = client.post(f"/deals/{deal_id}/reject", headers=_auth_headers(202))
    assert response.status_code == 200
    assert response.json()["state"] == DealState.REJECTED.value


def test_update_deal_requires_latest_proposal_counterparty(client: TestClient) -> None:
    deal_id = _create_listing_deal(client, advertiser_id=101, owner_id=202)

    own_update = client.patch(
        f"/deals/{deal_id}",
        json={"creative_text": "Advertiser edit"},
        headers=_auth_headers(101),
    )
    assert own_update.status_code == 409

    counterparty_update = client.patch(
        f"/deals/{deal_id}",
        json={"creative_text": "Owner edit"},
        headers=_auth_headers(202),
    )
    assert counterparty_update.status_code == 200


def test_update_deal_proposal_event_stores_full_snapshot(
    client: TestClient, db_engine
) -> None:
    deal_id = _create_listing_deal(client, advertiser_id=101, owner_id=202)

    response = client.patch(
        f"/deals/{deal_id}",
        json={"creative_text": "Owner update"},
        headers=_auth_headers(202),
    )
    assert response.status_code == 200

    with Session(db_engine) as session:
        proposal_events = session.exec(
            select(DealEvent)
            .where(DealEvent.deal_id == deal_id)
            .where(DealEvent.event_type == "proposal")
            .order_by(DealEvent.created_at.desc(), DealEvent.id.desc())
        ).all()
        latest = proposal_events[0]
        payload = latest.payload or {}
        assert payload["creative_text"] == "Owner update"
        assert payload["price_ton"] == "10.00"
        assert payload["ad_type"] == "post"
        assert payload["placement_type"] == "post"
        assert payload["exclusive_hours"] == 1
        assert payload["retention_hours"] == 24
        assert payload["creative_media_type"] == "image"
        assert payload["creative_media_ref"] == "ref"
        assert "start_at" in payload
        assert "posting_params" in payload


def test_accept_campaign_application_creates_deal(
    client: TestClient, db_engine, monkeypatch
) -> None:
    calls: list[int] = []
    monkeypatch.setattr(
        "app.api.routes.campaign_applications.notify_campaign_offer_accepted",
        lambda **kwargs: calls.append(kwargs["deal"].id),
    )

    campaign_id = _create_campaign(client, advertiser_id=101, budget_ton="15.00")
    channel_id = _create_channel(client, owner_id=202, username="@ownerchannel")
    _mark_channel_verified(db_engine, channel_id)

    response = client.post(
        f"/campaigns/{campaign_id}/apply",
        json={
            "channel_id": channel_id,
            "proposed_format_label": "Post",
            "proposed_placement_type": "post",
            "proposed_exclusive_hours": 1,
            "proposed_retention_hours": 24,
        },
        headers=_auth_headers(202),
    )
    assert response.status_code == 201
    application_id = response.json()["id"]

    response = client.post(
        f"/campaigns/{campaign_id}/applications/{application_id}/accept",
        json={
            "price_ton": "15.00",
            "creative_text": "Campaign",
            "creative_media_type": "video",
            "creative_media_ref": "video-ref",
            "start_at": "2026-02-10T10:00:00+00:00",
            "posting_params": {"hour": 12},
        },
        headers=_auth_headers(101),
    )
    assert response.status_code == 201
    payload = response.json()
    assert payload["source_type"] == DealSourceType.CAMPAIGN.value
    assert payload["state"] == DealState.DRAFT.value
    assert payload["placement_type"] == "post"
    assert payload["exclusive_hours"] == 1
    assert payload["retention_hours"] == 24
    assert payload["scheduled_at"] == "2026-02-10T10:00:00"

    with Session(db_engine) as session:
        application = session.exec(
            select(CampaignApplication).where(CampaignApplication.id == application_id)
        ).one()
        assert application.status == "accepted"
    assert calls == [payload["id"]]


def test_campaign_accept_defaults_price_from_campaign_budget(
    client: TestClient, db_engine
) -> None:
    campaign_id = _create_campaign(client, advertiser_id=101, budget_ton="19.00")
    channel_id = _create_channel(client, owner_id=202, username="@ownerchannel_budget")
    _mark_channel_verified(db_engine, channel_id)

    apply_response = client.post(
        f"/campaigns/{campaign_id}/apply",
        json={
            "channel_id": channel_id,
            "proposed_format_label": "Post",
            "proposed_placement_type": "post",
            "proposed_exclusive_hours": 1,
            "proposed_retention_hours": 24,
        },
        headers=_auth_headers(202),
    )
    assert apply_response.status_code == 201

    accept_response = client.post(
        f"/campaigns/{campaign_id}/applications/{apply_response.json()['id']}/accept",
        json={
            "creative_text": "Campaign budget fallback",
            "creative_media_type": "image",
            "creative_media_ref": "budget-ref",
        },
        headers=_auth_headers(101),
    )
    assert accept_response.status_code == 201
    payload = accept_response.json()
    assert payload["price_ton"] == "19.00"
    assert payload["ad_type"] == "Post"


def test_accept_campaign_application_allows_multiple_deals_until_limit(
    client: TestClient, db_engine
) -> None:
    campaign_id = _create_campaign(client, advertiser_id=101, max_acceptances=2)
    first_channel_id = _create_channel(client, owner_id=202, username="@multiowner1")
    second_channel_id = _create_channel(client, owner_id=303, username="@multiowner2")
    _mark_channel_verified(db_engine, first_channel_id)
    _mark_channel_verified(db_engine, second_channel_id)

    first_apply = client.post(
        f"/campaigns/{campaign_id}/apply",
        json={
            "channel_id": first_channel_id,
            "proposed_format_label": "Post",
            "proposed_placement_type": "post",
            "proposed_exclusive_hours": 1,
            "proposed_retention_hours": 24,
        },
        headers=_auth_headers(202),
    )
    second_apply = client.post(
        f"/campaigns/{campaign_id}/apply",
        json={
            "channel_id": second_channel_id,
            "proposed_format_label": "Story",
            "proposed_placement_type": "story",
            "proposed_exclusive_hours": 1,
            "proposed_retention_hours": 24,
        },
        headers=_auth_headers(303),
    )
    assert first_apply.status_code == 201
    assert second_apply.status_code == 201

    first_accept = client.post(
        f"/campaigns/{campaign_id}/applications/{first_apply.json()['id']}/accept",
        json={
            "price_ton": "11.00",
            "ad_type": "Post",
            "creative_text": "Campaign one",
            "creative_media_type": "image",
            "creative_media_ref": "one-ref",
        },
        headers=_auth_headers(101),
    )
    second_accept = client.post(
        f"/campaigns/{campaign_id}/applications/{second_apply.json()['id']}/accept",
        json={
            "price_ton": "12.00",
            "ad_type": "Story",
            "creative_text": "Campaign two",
            "creative_media_type": "video",
            "creative_media_ref": "two-ref",
        },
        headers=_auth_headers(101),
    )
    assert first_accept.status_code == 201
    assert second_accept.status_code == 201

    with Session(db_engine) as session:
        deals = session.exec(select(Deal).where(Deal.campaign_id == campaign_id)).all()
        assert len(deals) == 2
        campaign = session.exec(
            select(CampaignRequest).where(CampaignRequest.id == campaign_id)
        ).one()
        assert campaign.lifecycle_state == "closed_by_limit"


def test_accept_campaign_application_blocks_after_limit(
    client: TestClient, db_engine
) -> None:
    campaign_id = _create_campaign(client, advertiser_id=101, max_acceptances=1)
    first_channel_id = _create_channel(client, owner_id=202, username="@limitowner1")
    second_channel_id = _create_channel(client, owner_id=303, username="@limitowner2")
    _mark_channel_verified(db_engine, first_channel_id)
    _mark_channel_verified(db_engine, second_channel_id)

    first_apply = client.post(
        f"/campaigns/{campaign_id}/apply",
        json={
            "channel_id": first_channel_id,
            "proposed_format_label": "Post",
            "proposed_placement_type": "post",
            "proposed_exclusive_hours": 1,
            "proposed_retention_hours": 24,
        },
        headers=_auth_headers(202),
    )
    second_apply = client.post(
        f"/campaigns/{campaign_id}/apply",
        json={
            "channel_id": second_channel_id,
            "proposed_format_label": "Story",
            "proposed_placement_type": "story",
            "proposed_exclusive_hours": 1,
            "proposed_retention_hours": 24,
        },
        headers=_auth_headers(303),
    )
    assert first_apply.status_code == 201
    assert second_apply.status_code == 201

    first_accept = client.post(
        f"/campaigns/{campaign_id}/applications/{first_apply.json()['id']}/accept",
        json={
            "price_ton": "11.00",
            "ad_type": "Post",
            "creative_text": "Campaign one",
            "creative_media_type": "image",
            "creative_media_ref": "one-ref",
        },
        headers=_auth_headers(101),
    )
    assert first_accept.status_code == 201

    second_accept = client.post(
        f"/campaigns/{campaign_id}/applications/{second_apply.json()['id']}/accept",
        json={
            "price_ton": "12.00",
            "ad_type": "Story",
            "creative_text": "Campaign two",
            "creative_media_type": "video",
            "creative_media_ref": "two-ref",
        },
        headers=_auth_headers(101),
    )
    assert second_accept.status_code == 409

    with Session(db_engine) as session:
        second_application = session.exec(
            select(CampaignApplication).where(
                CampaignApplication.id == second_apply.json()["id"]
            )
        ).one()
        assert second_application.status == "rejected"


def test_parallel_accept_requests_respect_max_acceptances(
    client: TestClient, db_engine
) -> None:
    if db_engine.dialect.name == "sqlite":
        pytest.skip(
            "Row-level lock semantics for FOR UPDATE are not available on SQLite."
        )

    campaign_id = _create_campaign(client, advertiser_id=101, max_acceptances=1)
    first_channel_id = _create_channel(client, owner_id=202, username="@parallelowner1")
    second_channel_id = _create_channel(
        client, owner_id=303, username="@parallelowner2"
    )
    _mark_channel_verified(db_engine, first_channel_id)
    _mark_channel_verified(db_engine, second_channel_id)

    first_apply = client.post(
        f"/campaigns/{campaign_id}/apply",
        json={
            "channel_id": first_channel_id,
            "proposed_format_label": "Post",
            "proposed_placement_type": "post",
            "proposed_exclusive_hours": 1,
            "proposed_retention_hours": 24,
        },
        headers=_auth_headers(202),
    )
    second_apply = client.post(
        f"/campaigns/{campaign_id}/apply",
        json={
            "channel_id": second_channel_id,
            "proposed_format_label": "Story",
            "proposed_placement_type": "story",
            "proposed_exclusive_hours": 1,
            "proposed_retention_hours": 24,
        },
        headers=_auth_headers(303),
    )
    assert first_apply.status_code == 201
    assert second_apply.status_code == 201

    def _accept(application_id: int):
        with TestClient(app) as thread_client:
            return thread_client.post(
                f"/campaigns/{campaign_id}/applications/{application_id}/accept",
                json={
                    "price_ton": "13.00",
                    "ad_type": "Post",
                    "creative_text": "Parallel",
                    "creative_media_type": "image",
                    "creative_media_ref": "parallel-ref",
                },
                headers=_auth_headers(101),
            ).status_code

    with ThreadPoolExecutor(max_workers=2) as pool:
        statuses = list(
            pool.map(
                _accept,
                [first_apply.json()["id"], second_apply.json()["id"]],
            )
        )

    assert statuses.count(201) == 1
    assert statuses.count(409) == 1

    with Session(db_engine) as session:
        deals = session.exec(select(Deal).where(Deal.campaign_id == campaign_id)).all()
        assert len(deals) == 1


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


def test_send_deal_message_blocked_after_reject(client: TestClient) -> None:
    deal_id = _create_listing_deal(client, advertiser_id=101, owner_id=202)

    reject_response = client.post(
        f"/deals/{deal_id}/reject", headers=_auth_headers(202)
    )
    assert reject_response.status_code == 200
    assert reject_response.json()["state"] == DealState.REJECTED.value

    response = client.post(
        f"/deals/{deal_id}/messages",
        json={"text": "Hello after reject"},
        headers=_auth_headers(101),
    )
    assert response.status_code == 409


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

    response = client.get(
        "/deals?role=owner&state=CREATIVE_SUBMITTED&page=1&page_size=20",
        headers=_auth_headers(202),
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    assert payload["items"][0]["id"] == deal_id_one

    response = client.get(
        "/deals?role=owner&page=1&page_size=1", headers=_auth_headers(202)
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["page_size"] == 1
    assert len(payload["items"]) == 1


def test_deal_detail_participant_fields(client: TestClient, db_engine) -> None:
    deal_id = _create_listing_deal(client, advertiser_id=101, owner_id=202)

    with Session(db_engine) as session:
        deal = session.exec(select(Deal).where(Deal.id == deal_id)).one()
        channel = session.exec(
            select(Channel).where(Channel.id == deal.channel_id)
        ).one()
        channel.title = "Channel Title"
        session.add(channel)
        advertiser = session.exec(
            select(User).where(User.id == deal.advertiser_id)
        ).one()
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
        proposal = session.exec(
            select(DealEvent)
            .where(DealEvent.deal_id == deal_id)
            .where(DealEvent.event_type == "proposal")
            .order_by(DealEvent.created_at.desc(), DealEvent.id.desc())
        ).first()
        assert proposal is not None
        proposal.created_at = datetime(2026, 2, 9, 9, 0, tzinfo=timezone.utc)
        session.add(proposal)

        escrow = DealEscrow(
            deal_id=deal.id,
            state="CREATED",
            subwallet_id=999,
            escrow_network="testnet",
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
                created_at=datetime(2026, 2, 9, 10, 0, tzinfo=timezone.utc),
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
                created_at=datetime(2026, 2, 9, 11, 0, tzinfo=timezone.utc),
            )
        )
        session.commit()

    response = client.get(
        f"/deals/{deal_id}/events?limit=2", headers=_auth_headers(101)
    )
    assert response.status_code == 200
    payload = response.json()
    assert len(payload["items"]) == 2
    assert payload["items"][0]["event_type"] == "created"
    assert payload["items"][1]["event_type"] == "transition"
    assert payload["next_cursor"] is not None

    response_page_two = client.get(
        f"/deals/{deal_id}/events",
        headers=_auth_headers(101),
        params={"cursor": payload["next_cursor"], "limit": 2},
    )
    assert response_page_two.status_code == 200
    payload_two = response_page_two.json()
    assert len(payload_two["items"]) == 1
    assert payload_two["items"][0]["event_type"] == "proposal"


def test_creative_endpoints_flow(client: TestClient, db_engine) -> None:
    deal_id = _create_listing_deal(client, advertiser_id=101, owner_id=202)
    with Session(db_engine) as session:
        deal = session.exec(select(Deal).where(Deal.id == deal_id)).one()
        deal.state = DealState.ACCEPTED.value
        session.add(deal)
        session.commit()

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

    response = client.post(
        f"/deals/{deal_id}/creative/request-edits", headers=_auth_headers(101)
    )
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

    response = client.post(
        f"/deals/{deal_id}/creative/approve", headers=_auth_headers(101)
    )
    assert response.status_code == 200
    assert response.json()["state"] == DealState.CREATIVE_APPROVED.value


def test_creative_upload_endpoint(client: TestClient, monkeypatch, db_engine) -> None:
    def fake_post(url: str, data: dict, files: dict):
        class DummyResponse:
            status_code = 200

            def json(self) -> dict:
                return {"ok": True, "result": {"photo": [{"file_id": "file-1"}]}}

        return DummyResponse()

    monkeypatch.setattr(bot_api.httpx, "post", fake_post)

    deal_id = _create_listing_deal(client, advertiser_id=101, owner_id=202)
    with Session(db_engine) as session:
        deal = session.exec(select(Deal).where(Deal.id == deal_id)).one()
        deal.state = DealState.ACCEPTED.value
        session.add(deal)
        session.commit()

    response = client.post(
        f"/deals/{deal_id}/creative/upload",
        files={"file": ("photo.jpg", b"data", "image/jpeg")},
        headers=_auth_headers(202),
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["creative_media_ref"] == "file-1"
    assert payload["creative_media_type"] == "image"


def test_proposal_media_upload_requires_latest_counterparty(
    client: TestClient, monkeypatch
) -> None:
    def fake_post(url: str, data: dict, files: dict):
        class DummyResponse:
            status_code = 200

            def json(self) -> dict:
                return {
                    "ok": True,
                    "result": {"photo": [{"file_id": "proposal-file-1"}]},
                }

        return DummyResponse()

    monkeypatch.setattr(bot_api.httpx, "post", fake_post)

    deal_id = _create_listing_deal(client, advertiser_id=101, owner_id=202)

    own_proposal_upload = client.post(
        f"/deals/{deal_id}/proposal/upload",
        files={"file": ("photo.jpg", b"data", "image/jpeg")},
        headers=_auth_headers(101),
    )
    assert own_proposal_upload.status_code == 409

    counterparty_upload = client.post(
        f"/deals/{deal_id}/proposal/upload",
        files={"file": ("photo.jpg", b"data", "image/jpeg")},
        headers=_auth_headers(202),
    )
    assert counterparty_upload.status_code == 200
    payload = counterparty_upload.json()
    assert payload["creative_media_ref"] == "proposal-file-1"
    assert payload["creative_media_type"] == "image"


def test_proposal_media_preview_endpoint(client: TestClient, monkeypatch) -> None:
    def fake_post(url: str, json: dict):
        class DummyResponse:
            status_code = 200

            def json(self) -> dict:
                return {"ok": True, "result": {"file_path": "photos/preview-1.jpg"}}

        return DummyResponse()

    def fake_get(url: str):
        class DummyResponse:
            status_code = 200
            content = b"image-bytes"
            headers = {"content-type": "image/jpeg"}
            text = "ok"

        return DummyResponse()

    monkeypatch.setattr(bot_api.httpx, "post", fake_post)
    monkeypatch.setattr(bot_api.httpx, "get", fake_get)

    deal_id = _create_listing_deal(client, advertiser_id=101, owner_id=202)

    response = client.get(
        f"/deals/{deal_id}/proposal/media",
        params={"media_ref": "ref"},
        headers=_auth_headers(101),
    )
    assert response.status_code == 200
    assert response.content == b"image-bytes"
    assert response.headers["content-type"].startswith("image/jpeg")
