from __future__ import annotations

import hashlib
import hmac
import json
import time
from datetime import datetime, timezone
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
from app.models.channel_stats_snapshot import ChannelStatsSnapshot
from app.models.user import User
from app.settings import Settings
from shared.db.base import SQLModel
import shared.telegram.bot_api as bot_api

BOT_TOKEN = "test-bot-token"


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
            _env_file=None, TELEGRAM_BOT_TOKEN=BOT_TOKEN, TELEGRAM_MEDIA_CHANNEL_ID=123
        )

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_settings_dep] = override_get_settings
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def _user_payload(user_id: int) -> str:
    return json.dumps({"id": user_id, "first_name": "Ada", "username": "ada"})


def _auth_headers(user_id: int) -> dict[str, str]:
    auth_date = str(int(time.time()))
    init_data = build_init_data(
        {"auth_date": auth_date, "user": _user_payload(user_id)}
    )
    return {"X-Telegram-Init-Data": init_data}


def _create_campaign(
    client: TestClient,
    *,
    user_id: int,
    title: str = "Title",
    max_acceptances: int | None = None,
) -> int:
    payload: dict[str, object] = {"title": title, "brief": "Brief"}
    if max_acceptances is not None:
        payload["max_acceptances"] = max_acceptances
    response = client.post(
        "/campaigns",
        json=payload,
        headers=_auth_headers(user_id),
    )
    assert response.status_code == 201
    return response.json()["id"]


def _create_channel(client: TestClient, *, owner_id: int, username: str) -> int:
    response = client.post(
        "/channels",
        json={"username": username},
        headers=_auth_headers(owner_id),
    )
    assert response.status_code == 201
    return response.json()["id"]


def _mark_channel_verified(db_engine, channel_id: int) -> None:
    with Session(db_engine) as session:
        channel = session.exec(select(Channel).where(Channel.id == channel_id)).one()
        channel.is_verified = True
        session.add(channel)
        session.commit()


def _seed_snapshot(db_engine, channel_id: int) -> None:
    with Session(db_engine) as session:
        session.add(
            ChannelStatsSnapshot(
                channel_id=channel_id,
                avg_views=120,
                language_stats={"en": 0.6, "es": 0.2},
                premium_stats={"premium_ratio": 0.25},
                created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
            )
        )
        session.commit()


def test_create_campaign_success(client: TestClient, db_engine) -> None:
    response = client.post(
        "/campaigns",
        json={"title": "Launch", "brief": "Details"},
        headers=_auth_headers(123),
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["title"] == "Launch"
    assert payload["brief"] == "Details"
    assert payload["is_active"] is True
    assert payload["lifecycle_state"] == "active"
    assert payload["max_acceptances"] == 10
    assert payload["hidden_at"] is None

    with Session(db_engine) as session:
        campaign = session.exec(select(CampaignRequest)).one()
        user = session.exec(select(User).where(User.telegram_user_id == 123)).one()
        assert campaign.advertiser_id == user.id
        assert campaign.lifecycle_state == "active"
        assert campaign.max_acceptances == 10


def test_invalid_max_acceptances_rejected(client: TestClient) -> None:
    response = client.post(
        "/campaigns",
        json={"title": "Launch", "brief": "Details", "max_acceptances": 0},
        headers=_auth_headers(123),
    )

    assert response.status_code == 400


def test_list_campaigns_returns_only_mine(client: TestClient) -> None:
    _create_campaign(client, user_id=123, title="Mine")
    _create_campaign(client, user_id=456, title="Other")

    response = client.get("/campaigns", headers=_auth_headers(123))

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    assert len(payload["items"]) == 1
    assert payload["items"][0]["title"] == "Mine"


def test_owner_discover_campaigns_filters_by_active_and_search(
    client: TestClient, db_engine
) -> None:
    matching_campaign_id = _create_campaign(client, user_id=123, title="Summer Launch")
    _create_campaign(client, user_id=456, title="Winter Campaign")
    hidden_campaign_id = _create_campaign(client, user_id=789, title="Summer Hidden")
    closed_campaign_id = _create_campaign(client, user_id=999, title="Summer Closed")

    hidden_response = client.delete(
        f"/campaigns/{hidden_campaign_id}", headers=_auth_headers(789)
    )
    assert hidden_response.status_code == 204

    with Session(db_engine) as session:
        closed_campaign = session.exec(
            select(CampaignRequest).where(CampaignRequest.id == closed_campaign_id)
        ).one()
        closed_campaign.lifecycle_state = "closed_by_limit"
        closed_campaign.is_active = False
        session.add(closed_campaign)
        session.commit()

    response = client.get(
        "/campaigns/discover?search=Summer", headers=_auth_headers(456)
    )
    assert response.status_code == 200

    payload = response.json()
    assert payload["total"] == 1
    assert len(payload["items"]) == 1
    item = payload["items"][0]
    assert item["id"] == matching_campaign_id
    assert item["title"] == "Summer Launch"
    assert item["advertiser_id"] > 0
    assert item["max_acceptances"] == 10
    assert "budget_ton" in item
    assert "min_subscribers" in item
    assert "min_avg_views" in item


def test_advertiser_offers_inbox_scoped_sorted_and_excludes_hidden(
    client: TestClient, db_engine
) -> None:
    advertiser_campaign_id = _create_campaign(
        client, user_id=123, title="Visible Campaign"
    )
    hidden_campaign_id = _create_campaign(client, user_id=123, title="Hidden Campaign")
    other_advertiser_campaign_id = _create_campaign(
        client, user_id=999, title="Other Advertiser"
    )

    channel_a = _create_channel(client, owner_id=456, username="@offers_a")
    channel_b = _create_channel(client, owner_id=789, username="@offers_b")
    channel_c = _create_channel(client, owner_id=987, username="@offers_c")
    channel_d = _create_channel(client, owner_id=654, username="@offers_d")
    _mark_channel_verified(db_engine, channel_a)
    _mark_channel_verified(db_engine, channel_b)
    _mark_channel_verified(db_engine, channel_c)
    _mark_channel_verified(db_engine, channel_d)

    visible_old = client.post(
        f"/campaigns/{advertiser_campaign_id}/apply",
        json={
            "channel_id": channel_a,
            "proposed_format_label": "Post",
            "proposed_placement_type": "post",
            "proposed_exclusive_hours": 1,
            "proposed_retention_hours": 24,
        },
        headers=_auth_headers(456),
    )
    visible_new = client.post(
        f"/campaigns/{advertiser_campaign_id}/apply",
        json={
            "channel_id": channel_b,
            "proposed_format_label": "Story",
            "proposed_placement_type": "story",
            "proposed_exclusive_hours": 1,
            "proposed_retention_hours": 24,
        },
        headers=_auth_headers(789),
    )
    hidden_offer = client.post(
        f"/campaigns/{advertiser_campaign_id}/apply",
        json={
            "channel_id": channel_c,
            "proposed_format_label": "Post",
            "proposed_placement_type": "post",
            "proposed_exclusive_hours": 1,
            "proposed_retention_hours": 24,
        },
        headers=_auth_headers(987),
    )
    hidden_campaign_offer = client.post(
        f"/campaigns/{hidden_campaign_id}/apply",
        json={
            "channel_id": channel_d,
            "proposed_format_label": "Story",
            "proposed_placement_type": "story",
            "proposed_exclusive_hours": 1,
            "proposed_retention_hours": 24,
        },
        headers=_auth_headers(654),
    )
    other_advertiser_offer = client.post(
        f"/campaigns/{other_advertiser_campaign_id}/apply",
        json={
            "channel_id": channel_a,
            "proposed_format_label": "Post",
            "proposed_placement_type": "post",
            "proposed_exclusive_hours": 1,
            "proposed_retention_hours": 24,
        },
        headers=_auth_headers(456),
    )
    assert visible_old.status_code == 201
    assert visible_new.status_code == 201
    assert hidden_offer.status_code == 201
    assert hidden_campaign_offer.status_code == 201
    assert other_advertiser_offer.status_code == 201

    hidden_offer_id = hidden_offer.json()["id"]
    with Session(db_engine) as session:
        offer = session.exec(
            select(CampaignApplication).where(CampaignApplication.id == hidden_offer_id)
        ).one()
        offer.hidden_at = datetime.now(timezone.utc)
        session.add(offer)
        session.commit()

    hide_campaign_response = client.delete(
        f"/campaigns/{hidden_campaign_id}", headers=_auth_headers(123)
    )
    assert hide_campaign_response.status_code == 204

    advertiser_response = client.get("/campaigns/offers", headers=_auth_headers(123))
    assert advertiser_response.status_code == 200
    advertiser_payload = advertiser_response.json()
    assert advertiser_payload["total"] == 2
    assert [item["application_id"] for item in advertiser_payload["items"]] == [
        visible_new.json()["id"],
        visible_old.json()["id"],
    ]
    assert all(
        item["campaign_id"] == advertiser_campaign_id
        for item in advertiser_payload["items"]
    )
    assert advertiser_payload["items"][0]["proposed_placement_type"] == "story"
    assert advertiser_payload["items"][0]["proposed_exclusive_hours"] == 1
    assert advertiser_payload["items"][0]["proposed_retention_hours"] == 24

    other_advertiser_response = client.get(
        "/campaigns/offers", headers=_auth_headers(999)
    )
    assert other_advertiser_response.status_code == 200
    other_payload = other_advertiser_response.json()
    assert other_payload["total"] == 1
    assert other_payload["items"][0]["campaign_id"] == other_advertiser_campaign_id


def test_view_campaign_success(client: TestClient) -> None:
    campaign_id = _create_campaign(client, user_id=123, title="Mine")

    response = client.get(f"/campaigns/{campaign_id}", headers=_auth_headers(123))

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == campaign_id
    assert payload["title"] == "Mine"


def test_view_campaign_not_mine_forbidden(client: TestClient) -> None:
    campaign_id = _create_campaign(client, user_id=123, title="Mine")

    response = client.get(f"/campaigns/{campaign_id}", headers=_auth_headers(456))

    assert response.status_code == 403


def test_delete_campaign_soft_hides_and_is_idempotent(
    client: TestClient, db_engine
) -> None:
    campaign_id = _create_campaign(client, user_id=123, title="ToHide")

    response = client.delete(f"/campaigns/{campaign_id}", headers=_auth_headers(123))
    assert response.status_code == 204

    response = client.delete(f"/campaigns/{campaign_id}", headers=_auth_headers(123))
    assert response.status_code == 204

    response = client.get(f"/campaigns/{campaign_id}", headers=_auth_headers(123))
    assert response.status_code == 404

    response = client.get("/campaigns", headers=_auth_headers(123))
    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 0
    assert payload["items"] == []

    with Session(db_engine) as session:
        campaign = session.exec(
            select(CampaignRequest).where(CampaignRequest.id == campaign_id)
        ).one()
        assert campaign.lifecycle_state == "hidden"
        assert campaign.is_active is False
        assert campaign.hidden_at is not None


def test_delete_campaign_cascades_hide_to_related_offers(
    client: TestClient, db_engine
) -> None:
    campaign_id = _create_campaign(client, user_id=123, title="Cascade")
    channel_id = _create_channel(client, owner_id=456, username="@cascadeowner")
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
        headers=_auth_headers(456),
    )
    assert apply_response.status_code == 201
    application_id = apply_response.json()["id"]

    delete_response = client.delete(
        f"/campaigns/{campaign_id}", headers=_auth_headers(123)
    )
    assert delete_response.status_code == 204

    applications_response = client.get(
        f"/campaigns/{campaign_id}/applications",
        headers=_auth_headers(123),
    )
    assert applications_response.status_code == 404

    with Session(db_engine) as session:
        application = session.exec(
            select(CampaignApplication).where(CampaignApplication.id == application_id)
        ).one()
        assert application.hidden_at is not None


def test_hidden_campaign_cannot_receive_applications(
    client: TestClient, db_engine
) -> None:
    campaign_id = _create_campaign(client, user_id=123, title="HideThenApply")
    channel_id = _create_channel(client, owner_id=456, username="@hideapply")
    _mark_channel_verified(db_engine, channel_id)

    delete_response = client.delete(
        f"/campaigns/{campaign_id}", headers=_auth_headers(123)
    )
    assert delete_response.status_code == 204

    response = client.post(
        f"/campaigns/{campaign_id}/apply",
        json={
            "channel_id": channel_id,
            "proposed_format_label": "Post",
            "proposed_placement_type": "post",
            "proposed_exclusive_hours": 1,
            "proposed_retention_hours": 24,
        },
        headers=_auth_headers(456),
    )
    assert response.status_code == 404


def test_invalid_dates_rejected(client: TestClient) -> None:
    response = client.post(
        "/campaigns",
        json={
            "title": "Launch",
            "brief": "Details",
            "start_at": "2026-01-10T00:00:00+00:00",
            "end_at": "2026-01-05T00:00:00+00:00",
        },
        headers=_auth_headers(123),
    )

    assert response.status_code == 400


def test_owner_apply_success(client: TestClient, db_engine, monkeypatch) -> None:
    calls: list[int] = []
    monkeypatch.setattr(
        "app.api.routes.campaign_applications.notify_campaign_offer_received",
        lambda **kwargs: calls.append(kwargs["application_id"]),
    )

    campaign_id = _create_campaign(client, user_id=123)
    channel_id = _create_channel(client, owner_id=456, username="@ownerchannel")
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
        headers=_auth_headers(456),
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["campaign_id"] == campaign_id
    assert payload["status"] == "submitted"
    assert payload["proposed_placement_type"] == "post"
    assert payload["proposed_exclusive_hours"] == 1
    assert payload["proposed_retention_hours"] == 24
    assert calls == [payload["id"]]


def test_advertiser_upload_offer_creative_success(
    client: TestClient, db_engine, monkeypatch
) -> None:
    def fake_post(url: str, data: dict, files: dict):
        class DummyResponse:
            status_code = 200

            def json(self) -> dict:
                return {
                    "ok": True,
                    "result": {"photo": [{"file_id": "campaign-file-1"}]},
                }

        return DummyResponse()

    monkeypatch.setattr(bot_api.httpx, "post", fake_post)

    campaign_id = _create_campaign(client, user_id=123)
    channel_id = _create_channel(client, owner_id=456, username="@creativeupload")
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
        headers=_auth_headers(456),
    )
    assert apply_response.status_code == 201
    application_id = apply_response.json()["id"]

    response = client.post(
        f"/campaigns/{campaign_id}/applications/{application_id}/creative/upload",
        files={"file": ("photo.jpg", b"data", "image/jpeg")},
        headers=_auth_headers(123),
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["creative_media_ref"] == "campaign-file-1"
    assert payload["creative_media_type"] == "image"


def test_offer_creative_upload_forbidden_for_non_advertiser(
    client: TestClient, db_engine
) -> None:
    campaign_id = _create_campaign(client, user_id=123)
    channel_id = _create_channel(client, owner_id=456, username="@creativeforbidden")
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
        headers=_auth_headers(456),
    )
    assert apply_response.status_code == 201
    application_id = apply_response.json()["id"]

    response = client.post(
        f"/campaigns/{campaign_id}/applications/{application_id}/creative/upload",
        files={"file": ("photo.jpg", b"data", "image/jpeg")},
        headers=_auth_headers(999),
    )
    assert response.status_code == 403


def test_non_owner_apply_forbidden(client: TestClient, db_engine) -> None:
    campaign_id = _create_campaign(client, user_id=123)
    channel_id = _create_channel(client, owner_id=456, username="@ownerchannel")
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
        headers=_auth_headers(789),
    )

    assert response.status_code == 403


def test_apply_unverified_channel_rejected(client: TestClient) -> None:
    campaign_id = _create_campaign(client, user_id=123)
    channel_id = _create_channel(client, owner_id=456, username="@ownerchannel")

    response = client.post(
        f"/campaigns/{campaign_id}/apply",
        json={
            "channel_id": channel_id,
            "proposed_format_label": "Post",
            "proposed_placement_type": "post",
            "proposed_exclusive_hours": 1,
            "proposed_retention_hours": 24,
        },
        headers=_auth_headers(456),
    )

    assert response.status_code == 400


def test_advertiser_lists_applications_success(client: TestClient, db_engine) -> None:
    campaign_id = _create_campaign(client, user_id=123)
    channel_id = _create_channel(client, owner_id=456, username="@ownerchannel")
    _mark_channel_verified(db_engine, channel_id)
    _seed_snapshot(db_engine, channel_id)

    apply_response = client.post(
        f"/campaigns/{campaign_id}/apply",
        json={
            "channel_id": channel_id,
            "proposed_format_label": "Post",
            "proposed_placement_type": "post",
            "proposed_exclusive_hours": 1,
            "proposed_retention_hours": 24,
        },
        headers=_auth_headers(456),
    )
    assert apply_response.status_code == 201

    response = client.get(
        f"/campaigns/{campaign_id}/applications",
        headers=_auth_headers(123),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    assert len(payload["items"]) == 1
    item = payload["items"][0]
    assert item["channel_id"] == channel_id
    assert item["stats"]["avg_views"] == 120
    assert item["stats"]["premium_ratio"] == 0.25
    assert item["stats"]["language_stats"] == {"en": 0.6}


def test_non_advertiser_listing_forbidden(client: TestClient, db_engine) -> None:
    campaign_id = _create_campaign(client, user_id=123)
    channel_id = _create_channel(client, owner_id=456, username="@ownerchannel")
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
        headers=_auth_headers(456),
    )
    assert apply_response.status_code == 201

    response = client.get(
        f"/campaigns/{campaign_id}/applications",
        headers=_auth_headers(456),
    )

    assert response.status_code == 403


def test_duplicate_apply_conflict(client: TestClient, db_engine) -> None:
    campaign_id = _create_campaign(client, user_id=123)
    channel_id = _create_channel(client, owner_id=456, username="@ownerchannel")
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
        headers=_auth_headers(456),
    )
    assert response.status_code == 201

    response = client.post(
        f"/campaigns/{campaign_id}/apply",
        json={
            "channel_id": channel_id,
            "proposed_format_label": "Post",
            "proposed_placement_type": "post",
            "proposed_exclusive_hours": 1,
            "proposed_retention_hours": 24,
        },
        headers=_auth_headers(456),
    )
    assert response.status_code == 409

    with Session(db_engine) as session:
        applications = session.exec(select(CampaignApplication)).all()
        assert len(applications) == 1


def test_closed_by_limit_blocks_future_applications(
    client: TestClient, db_engine
) -> None:
    campaign_id = _create_campaign(client, user_id=123, max_acceptances=1)
    first_channel_id = _create_channel(client, owner_id=456, username="@limitfirst")
    second_channel_id = _create_channel(client, owner_id=789, username="@limitsecond")
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
        headers=_auth_headers(456),
    )
    assert first_apply.status_code == 201
    first_application_id = first_apply.json()["id"]

    accept_response = client.post(
        f"/campaigns/{campaign_id}/applications/{first_application_id}/accept",
        json={
            "price_ton": "15.00",
            "ad_type": "Post",
            "creative_text": "Campaign",
            "creative_media_type": "video",
            "creative_media_ref": "video-ref",
        },
        headers=_auth_headers(123),
    )
    assert accept_response.status_code == 201

    blocked_apply = client.post(
        f"/campaigns/{campaign_id}/apply",
        json={
            "channel_id": second_channel_id,
            "proposed_format_label": "Post",
            "proposed_placement_type": "post",
            "proposed_exclusive_hours": 1,
            "proposed_retention_hours": 24,
        },
        headers=_auth_headers(789),
    )
    assert blocked_apply.status_code == 404

    with Session(db_engine) as session:
        campaign = session.exec(
            select(CampaignRequest).where(CampaignRequest.id == campaign_id)
        ).one()
        assert campaign.lifecycle_state == "closed_by_limit"
        assert campaign.is_active is False


def test_limit_reach_auto_rejects_remaining_submitted_offers(
    client: TestClient, db_engine
) -> None:
    campaign_id = _create_campaign(client, user_id=123, max_acceptances=1)
    first_channel_id = _create_channel(client, owner_id=456, username="@autoreject1")
    second_channel_id = _create_channel(client, owner_id=789, username="@autoreject2")
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
        headers=_auth_headers(456),
    )
    assert first_apply.status_code == 201
    first_application_id = first_apply.json()["id"]

    second_apply = client.post(
        f"/campaigns/{campaign_id}/apply",
        json={
            "channel_id": second_channel_id,
            "proposed_format_label": "Post",
            "proposed_placement_type": "post",
            "proposed_exclusive_hours": 1,
            "proposed_retention_hours": 24,
        },
        headers=_auth_headers(789),
    )
    assert second_apply.status_code == 201
    second_application_id = second_apply.json()["id"]

    accept_response = client.post(
        f"/campaigns/{campaign_id}/applications/{first_application_id}/accept",
        json={
            "price_ton": "15.00",
            "ad_type": "Post",
            "creative_text": "Campaign",
            "creative_media_type": "video",
            "creative_media_ref": "video-ref",
        },
        headers=_auth_headers(123),
    )
    assert accept_response.status_code == 201

    with Session(db_engine) as session:
        first_application = session.exec(
            select(CampaignApplication).where(
                CampaignApplication.id == first_application_id
            )
        ).one()
        second_application = session.exec(
            select(CampaignApplication).where(
                CampaignApplication.id == second_application_id
            )
        ).one()
        assert first_application.status == "accepted"
        assert second_application.status == "rejected"


def test_hidden_offers_are_excluded_from_offer_listing(
    client: TestClient, db_engine
) -> None:
    campaign_id = _create_campaign(client, user_id=123)
    first_channel_id = _create_channel(client, owner_id=456, username="@hiddenoffer1")
    second_channel_id = _create_channel(client, owner_id=789, username="@hiddenoffer2")
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
        headers=_auth_headers(456),
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
        headers=_auth_headers(789),
    )
    assert first_apply.status_code == 201
    assert second_apply.status_code == 201
    hidden_application_id = second_apply.json()["id"]

    with Session(db_engine) as session:
        application = session.exec(
            select(CampaignApplication).where(
                CampaignApplication.id == hidden_application_id
            )
        ).one()
        application.hidden_at = datetime.now(timezone.utc)
        session.add(application)
        session.commit()

    response = client.get(
        f"/campaigns/{campaign_id}/applications",
        headers=_auth_headers(123),
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    assert len(payload["items"]) == 1
