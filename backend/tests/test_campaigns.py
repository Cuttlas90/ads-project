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

BOT_TOKEN = "test-bot-token"


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
        return Settings(_env_file=None, TELEGRAM_BOT_TOKEN=BOT_TOKEN)

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_settings_dep] = override_get_settings
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def _user_payload(user_id: int) -> str:
    return json.dumps({"id": user_id, "first_name": "Ada", "username": "ada"})


def _auth_headers(user_id: int) -> dict[str, str]:
    auth_date = str(int(time.time()))
    init_data = build_init_data({"auth_date": auth_date, "user": _user_payload(user_id)})
    return {"X-Telegram-Init-Data": init_data}


def _create_campaign(client: TestClient, *, user_id: int, title: str = "Title") -> int:
    response = client.post(
        "/campaigns",
        json={"title": title, "brief": "Brief"},
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

    with Session(db_engine) as session:
        campaign = session.exec(select(CampaignRequest)).one()
        user = session.exec(select(User).where(User.telegram_user_id == 123)).one()
        assert campaign.advertiser_id == user.id


def test_list_campaigns_returns_only_mine(client: TestClient) -> None:
    _create_campaign(client, user_id=123, title="Mine")
    _create_campaign(client, user_id=456, title="Other")

    response = client.get("/campaigns", headers=_auth_headers(123))

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    assert len(payload["items"]) == 1
    assert payload["items"][0]["title"] == "Mine"


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


def test_owner_apply_success(client: TestClient, db_engine) -> None:
    campaign_id = _create_campaign(client, user_id=123)
    channel_id = _create_channel(client, owner_id=456, username="@ownerchannel")
    _mark_channel_verified(db_engine, channel_id)

    response = client.post(
        f"/campaigns/{campaign_id}/apply",
        json={"channel_id": channel_id, "proposed_format_label": "Post"},
        headers=_auth_headers(456),
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["campaign_id"] == campaign_id
    assert payload["status"] == "submitted"


def test_non_owner_apply_forbidden(client: TestClient, db_engine) -> None:
    campaign_id = _create_campaign(client, user_id=123)
    channel_id = _create_channel(client, owner_id=456, username="@ownerchannel")
    _mark_channel_verified(db_engine, channel_id)

    response = client.post(
        f"/campaigns/{campaign_id}/apply",
        json={"channel_id": channel_id, "proposed_format_label": "Post"},
        headers=_auth_headers(789),
    )

    assert response.status_code == 403


def test_apply_unverified_channel_rejected(client: TestClient) -> None:
    campaign_id = _create_campaign(client, user_id=123)
    channel_id = _create_channel(client, owner_id=456, username="@ownerchannel")

    response = client.post(
        f"/campaigns/{campaign_id}/apply",
        json={"channel_id": channel_id, "proposed_format_label": "Post"},
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
        json={"channel_id": channel_id, "proposed_format_label": "Post"},
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
        json={"channel_id": channel_id, "proposed_format_label": "Post"},
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
        json={"channel_id": channel_id, "proposed_format_label": "Post"},
        headers=_auth_headers(456),
    )
    assert response.status_code == 201

    response = client.post(
        f"/campaigns/{campaign_id}/apply",
        json={"channel_id": channel_id, "proposed_format_label": "Post"},
        headers=_auth_headers(456),
    )
    assert response.status_code == 409

    with Session(db_engine) as session:
        applications = session.exec(select(CampaignApplication)).all()
        assert len(applications) == 1
