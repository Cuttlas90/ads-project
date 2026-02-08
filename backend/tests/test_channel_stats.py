from __future__ import annotations

import hashlib
import hmac
import json
import time
from urllib.parse import urlencode

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, select

import app.api.routes.channels as channels_route
from app.api.deps import get_db, get_settings_dep
from app.main import app
from app.models.channel import Channel
from app.models.channel_stats_snapshot import ChannelStatsSnapshot
from app.models.listing import Listing
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
    return json.dumps({"id": user_id, "first_name": "Ada", "username": f"user_{user_id}"})


def _auth_headers(user_id: int) -> dict[str, str]:
    auth_date = str(int(time.time()))
    init_data = build_init_data({"auth_date": auth_date, "user": _user_payload(user_id)})
    return {"X-Telegram-Init-Data": init_data}


def _register_user(client: TestClient, *, user_id: int) -> None:
    response = client.get("/channels", headers=_auth_headers(user_id))
    assert response.status_code == 200


def _create_channel(client: TestClient, *, owner_id: int, username: str = "@stats_channel") -> int:
    response = client.post(
        "/channels",
        json={"username": username},
        headers=_auth_headers(owner_id),
    )
    assert response.status_code == 201
    return response.json()["id"]


def _seed_listing_for_channel(db_engine, *, channel_id: int, owner_telegram_id: int, active: bool = True) -> None:
    with Session(db_engine) as session:
        owner = session.exec(select(User).where(User.telegram_user_id == owner_telegram_id)).one()
        listing = Listing(channel_id=channel_id, owner_id=owner.id, is_active=active)
        session.add(listing)
        session.commit()


def _set_channel_verified(db_engine, *, channel_id: int, title: str = "Stats Channel") -> None:
    with Session(db_engine) as session:
        channel = session.exec(select(Channel).where(Channel.id == channel_id)).one()
        channel.is_verified = True
        channel.title = title
        session.add(channel)
        session.commit()


def _seed_snapshot(
    db_engine,
    *,
    channel_id: int,
    subscribers: int | None = 1200,
    avg_views: int | None = 450,
    raw_stats: dict | None = None,
    premium_stats: dict | None = None,
) -> None:
    with Session(db_engine) as session:
        session.add(
            ChannelStatsSnapshot(
                channel_id=channel_id,
                subscribers=subscribers,
                avg_views=avg_views,
                raw_stats=raw_stats,
                premium_stats=premium_stats,
            )
        )
        session.commit()


def test_stats_endpoint_allows_marketplace_advertiser_access(client: TestClient, db_engine) -> None:
    channel_id = _create_channel(client, owner_id=123, username="@marketplace_stats")
    _set_channel_verified(db_engine, channel_id=channel_id)
    _seed_listing_for_channel(db_engine, channel_id=channel_id, owner_telegram_id=123)
    _seed_snapshot(db_engine, channel_id=channel_id)

    response = client.get(f"/channels/{channel_id}/stats", headers=_auth_headers(999))

    assert response.status_code == 200
    payload = response.json()
    assert payload["channel_id"] == channel_id
    assert payload["snapshot_available"] is True
    assert payload["read_only"] is True


def test_stats_endpoint_allows_owner_manager_read_only(client: TestClient, db_engine) -> None:
    channel_id = _create_channel(client, owner_id=123, username="@owner_manager_stats")
    _seed_snapshot(db_engine, channel_id=channel_id, subscribers=500, avg_views=200)

    _register_user(client, user_id=456)
    add_manager = client.post(
        f"/channels/{channel_id}/managers",
        json={"telegram_user_id": 456},
        headers=_auth_headers(123),
    )
    assert add_manager.status_code == 201

    response = client.get(f"/channels/{channel_id}/stats", headers=_auth_headers(456))

    assert response.status_code == 200
    assert response.json()["read_only"] is True


def test_stats_endpoint_disallows_non_eligible_non_member(client: TestClient, db_engine) -> None:
    channel_id = _create_channel(client, owner_id=123, username="@private_stats")
    _seed_snapshot(db_engine, channel_id=channel_id)

    response = client.get(f"/channels/{channel_id}/stats", headers=_auth_headers(999))

    assert response.status_code == 404


def test_stats_endpoint_normalizes_chart_markers_and_missing_metrics(client: TestClient, db_engine) -> None:
    channel_id = _create_channel(client, owner_id=123, username="@normalize_stats")
    _seed_snapshot(
        db_engine,
        channel_id=channel_id,
        raw_stats={
            "statistics": {
                "views_per_post": {"current": 320, "previous": 250},
                "shares_per_post": None,
                "growth_graph": {"_": "StatsGraph", "json": {"x": [1, 2], "y": [3, 4]}},
                "interactions_graph": {"_": "StatsGraphAsync", "token": "graph-token"},
                "premium_graph": {"_": "StatsGraphError", "error": "Not enough data"},
                "broken_graph": None,
            }
        },
    )

    response = client.get(f"/channels/{channel_id}/stats", headers=_auth_headers(123))

    assert response.status_code == 200
    payload = response.json()

    charts = {item["key"]: item for item in payload["chart_metrics"]}
    assert charts["growth_graph"]["availability"] == "ready"
    assert charts["growth_graph"]["data"] == {"x": [1, 2], "y": [3, 4]}
    assert charts["interactions_graph"]["availability"] == "async_pending"
    assert charts["interactions_graph"]["token"] == "graph-token"
    assert charts["premium_graph"]["availability"] == "error"
    assert charts["premium_graph"]["reason"] == "Not enough data"
    assert charts["broken_graph"]["availability"] == "missing"

    scalars = {item["key"]: item for item in payload["scalar_metrics"]}
    assert scalars["views_per_post"]["availability"] == "ready"
    assert scalars["views_per_post"]["value"] == 320
    assert scalars["shares_per_post"]["availability"] == "missing"


def test_stats_endpoint_prefers_premium_graph_over_boosts(client: TestClient, db_engine) -> None:
    channel_id = _create_channel(client, owner_id=123, username="@premium_precedence")
    _seed_snapshot(
        db_engine,
        channel_id=channel_id,
        raw_stats={
            "statistics": {
                "premium_graph": {"_": "StatsPercentValue", "part": 10, "total": 100},
            },
            "boosts_status": {
                "_": "BoostsStatus",
                "premium_audience": {"_": "StatsPercentValue", "part": 56, "total": 4511},
            },
        },
        premium_stats={"premium_ratio": 0.77},
    )

    response = client.get(f"/channels/{channel_id}/stats", headers=_auth_headers(123))

    assert response.status_code == 200
    payload = response.json()["premium_audience"]
    assert payload["availability"] == "ready"
    assert payload["premium_ratio"] == pytest.approx(0.1)
    assert payload["part"] == 10
    assert payload["total"] == 100


def test_stats_endpoint_falls_back_to_boosts_premium_audience(client: TestClient, db_engine) -> None:
    channel_id = _create_channel(client, owner_id=123, username="@premium_boosts")
    _seed_snapshot(
        db_engine,
        channel_id=channel_id,
        raw_stats={
            "statistics": {},
            "boosts_status": {
                "_": "BoostsStatus",
                "premium_audience": {"_": "StatsPercentValue", "part": 56, "total": 4511},
            },
        },
    )

    response = client.get(f"/channels/{channel_id}/stats", headers=_auth_headers(123))

    assert response.status_code == 200
    payload = response.json()["premium_audience"]
    assert payload["availability"] == "ready"
    assert payload["premium_ratio"] == pytest.approx(56 / 4511)
    assert payload["part"] == 56
    assert payload["total"] == 4511


def test_stats_endpoint_does_not_trigger_telegram_clients_on_read(client: TestClient, db_engine, monkeypatch) -> None:
    channel_id = _create_channel(client, owner_id=123, username="@no_telegram_read")
    _set_channel_verified(db_engine, channel_id=channel_id)
    _seed_listing_for_channel(db_engine, channel_id=channel_id, owner_telegram_id=123)
    _seed_snapshot(db_engine, channel_id=channel_id)

    class FailingTelegramService:
        def __init__(self, *_args, **_kwargs) -> None:
            raise AssertionError("Stats endpoint must not initialize Telegram clients")

    monkeypatch.setattr(channels_route, "TelegramClientService", FailingTelegramService)

    response = client.get(f"/channels/{channel_id}/stats", headers=_auth_headers(999))
    assert response.status_code == 200
