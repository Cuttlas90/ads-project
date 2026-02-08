from __future__ import annotations

import hashlib
import hmac
import json
import time
from datetime import datetime, timezone
from decimal import Decimal
from urllib.parse import urlencode

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlmodel import Session

from app.api.deps import get_db, get_settings_dep
from app.main import app
from app.models.channel import Channel
from app.models.channel_stats_snapshot import ChannelStatsSnapshot
from app.models.listing import Listing
from app.models.listing_format import ListingFormat
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


def _seed_listing(
    session: Session,
    *,
    telegram_user_id: int,
    username: str,
    title: str,
    is_verified: bool,
    is_active: bool,
    subscribers: int | None,
    avg_views: int | None,
    language_stats: dict | None,
    premium_stats: dict | None,
    formats: list[tuple[str, str]],
    created_at: datetime,
) -> Listing:
    user = User(telegram_user_id=telegram_user_id, username="user")
    channel = Channel(
        username=username,
        title=title,
        is_verified=is_verified,
        created_at=created_at,
        updated_at=created_at,
    )
    session.add(user)
    session.add(channel)
    session.flush()

    listing = Listing(
        channel_id=channel.id,
        owner_id=user.id,
        is_active=is_active,
        created_at=created_at,
        updated_at=created_at,
    )
    session.add(listing)
    session.flush()

    for label, price in formats:
        session.add(ListingFormat(listing_id=listing.id, label=label, price=Decimal(price)))

    session.add(
        ChannelStatsSnapshot(
            channel_id=channel.id,
            subscribers=subscribers,
            avg_views=avg_views,
            language_stats=language_stats,
            premium_stats=premium_stats,
            created_at=created_at,
        )
    )
    session.commit()
    return listing


def test_marketplace_excludes_unverified_or_inactive(client: TestClient, db_engine) -> None:
    created_at = datetime(2025, 1, 1, tzinfo=timezone.utc)
    with Session(db_engine) as session:
        _seed_listing(
            session,
            telegram_user_id=1,
            username="verified",
            title="Verified",
            is_verified=True,
            is_active=True,
            subscribers=100,
            avg_views=50,
            language_stats={"en": 0.8},
            premium_stats={"premium_ratio": 0.2},
            formats=[("Post", "10.00")],
            created_at=created_at,
        )
        _seed_listing(
            session,
            telegram_user_id=2,
            username="inactive",
            title="Inactive",
            is_verified=True,
            is_active=False,
            subscribers=200,
            avg_views=100,
            language_stats={"en": 0.9},
            premium_stats={"premium_ratio": 0.2},
            formats=[("Post", "20.00")],
            created_at=created_at,
        )
        _seed_listing(
            session,
            telegram_user_id=3,
            username="unverified",
            title="Unverified",
            is_verified=False,
            is_active=True,
            subscribers=300,
            avg_views=150,
            language_stats={"en": 0.9},
            premium_stats={"premium_ratio": 0.2},
            formats=[("Post", "30.00")],
            created_at=created_at,
        )

    response = client.get("/marketplace/listings", headers=_auth_headers(123))

    assert response.status_code == 200
    payload = response.json()
    assert len(payload["items"]) == 1
    assert "channel_id" in payload["items"][0]
    assert isinstance(payload["items"][0]["channel_id"], int)
    assert payload["items"][0]["channel_username"] == "verified"


def test_marketplace_filters_and_search(client: TestClient, db_engine) -> None:
    created_at = datetime(2025, 1, 1, tzinfo=timezone.utc)
    with Session(db_engine) as session:
        _seed_listing(
            session,
            telegram_user_id=1,
            username="alpha",
            title="Alpha Channel",
            is_verified=True,
            is_active=True,
            subscribers=1000,
            avg_views=200,
            language_stats={"en": 0.8},
            premium_stats={"premium_ratio": 0.3},
            formats=[("Post", "10.00"), ("Story", "100.00")],
            created_at=created_at,
        )
        _seed_listing(
            session,
            telegram_user_id=2,
            username="beta",
            title="Beta Channel",
            is_verified=True,
            is_active=True,
            subscribers=5000,
            avg_views=800,
            language_stats={"fa": 0.2},
            premium_stats={"premium_ratio": 0.05},
            formats=[("Post", "50.00")],
            created_at=created_at,
        )

    response = client.get(
        "/marketplace/listings?min_price=5&max_price=20&min_subscribers=500&search=alpha",
        headers=_auth_headers(123),
    )

    assert response.status_code == 200
    payload = response.json()
    assert len(payload["items"]) == 1
    assert payload["items"][0]["channel_username"] == "alpha"
    assert payload["items"][0]["formats"][0]["format_id"] == payload["items"][0]["formats"][0]["id"]


def test_marketplace_sort_by_price(client: TestClient, db_engine) -> None:
    created_at = datetime(2025, 1, 1, tzinfo=timezone.utc)
    with Session(db_engine) as session:
        _seed_listing(
            session,
            telegram_user_id=1,
            username="cheap",
            title="Cheap Channel",
            is_verified=True,
            is_active=True,
            subscribers=100,
            avg_views=50,
            language_stats={"en": 0.8},
            premium_stats={"premium_ratio": 0.2},
            formats=[("Post", "5.00"), ("Story", "25.00")],
            created_at=created_at,
        )
        _seed_listing(
            session,
            telegram_user_id=2,
            username="expensive",
            title="Expensive Channel",
            is_verified=True,
            is_active=True,
            subscribers=200,
            avg_views=100,
            language_stats={"en": 0.8},
            premium_stats={"premium_ratio": 0.2},
            formats=[("Post", "50.00")],
            created_at=created_at,
        )

    response = client.get("/marketplace/listings?sort=price", headers=_auth_headers(123))

    assert response.status_code == 200
    payload = response.json()
    assert payload["items"][0]["channel_username"] == "cheap"
    assert payload["items"][1]["channel_username"] == "expensive"


def test_marketplace_invalid_params_return_400(client: TestClient) -> None:
    response = client.get("/marketplace/listings?min_price=not-a-number")

    assert response.status_code == 400


def test_marketplace_premium_filter_excludes_missing_stats(client: TestClient, db_engine) -> None:
    created_at = datetime(2025, 1, 1, tzinfo=timezone.utc)
    with Session(db_engine) as session:
        _seed_listing(
            session,
            telegram_user_id=1,
            username="premium",
            title="Premium Channel",
            is_verified=True,
            is_active=True,
            subscribers=100,
            avg_views=50,
            language_stats={"en": 0.8},
            premium_stats={"premium_ratio": 0.2},
            formats=[("Post", "5.00")],
            created_at=created_at,
        )
        _seed_listing(
            session,
            telegram_user_id=2,
            username="unknown",
            title="Unknown Channel",
            is_verified=True,
            is_active=True,
            subscribers=100,
            avg_views=50,
            language_stats={"en": 0.8},
            premium_stats=None,
            formats=[("Post", "5.00")],
            created_at=created_at,
        )

    response = client.get("/marketplace/listings?min_premium_pct=0.1")

    assert response.status_code == 200
    payload = response.json()
    usernames = [item["channel_username"] for item in payload["items"]]
    assert "premium" in usernames
    assert "unknown" not in usernames
