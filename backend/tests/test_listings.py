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
from app.models.channel_member import ChannelMember
from app.models.listing import Listing
from app.models.listing_format import ListingFormat
from app.models.user import User
from app.schemas.channel import ChannelRole
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


def _ensure_user(client: TestClient, user_id: int) -> None:
    client.get("/channels", headers=_auth_headers(user_id))


def _create_channel(client: TestClient, owner_id: int, username: str = "@channel") -> int:
    response = client.post(
        "/channels",
        json={"username": username},
        headers=_auth_headers(owner_id),
    )
    return response.json()["id"]


def _create_listing(client: TestClient, channel_id: int, owner_id: int) -> int:
    response = client.post(
        "/listings",
        json={"channel_id": channel_id},
        headers=_auth_headers(owner_id),
    )
    return response.json()["id"]


def _create_listing_format(client: TestClient, listing_id: int, owner_id: int) -> int:
    response = client.post(
        f"/listings/{listing_id}/formats",
        json={"label": "Post", "price": "10.00"},
        headers=_auth_headers(owner_id),
    )
    return response.json()["id"]


def test_create_listing_success(client: TestClient, db_engine) -> None:
    channel_id = _create_channel(client, owner_id=123, username="@ownerchannel")

    response = client.post(
        "/listings",
        json={"channel_id": channel_id},
        headers=_auth_headers(123),
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["channel_id"] == channel_id
    assert payload["is_active"] is True

    with Session(db_engine) as session:
        user = session.exec(select(User).where(User.telegram_user_id == 123)).one()
        listing = session.exec(select(Listing).where(Listing.channel_id == channel_id)).one()
        assert listing.owner_id == user.id


def test_create_listing_duplicate_conflict(client: TestClient) -> None:
    channel_id = _create_channel(client, owner_id=123, username="@ownerchannel")

    client.post(
        "/listings",
        json={"channel_id": channel_id},
        headers=_auth_headers(123),
    )

    response = client.post(
        "/listings",
        json={"channel_id": channel_id},
        headers=_auth_headers(123),
    )

    assert response.status_code == 409


def test_create_listing_non_owner_forbidden(client: TestClient) -> None:
    channel_id = _create_channel(client, owner_id=123, username="@ownerchannel")
    _ensure_user(client, user_id=456)

    response = client.post(
        "/listings",
        json={"channel_id": channel_id},
        headers=_auth_headers(456),
    )

    assert response.status_code == 403


def test_manager_cannot_create_listing(client: TestClient) -> None:
    channel_id = _create_channel(client, owner_id=123, username="@ownerchannel")
    _ensure_user(client, user_id=456)

    response = client.post(
        f"/channels/{channel_id}/managers",
        json={"telegram_user_id": 456},
        headers=_auth_headers(123),
    )
    assert response.status_code == 201

    response = client.post(
        "/listings",
        json={"channel_id": channel_id},
        headers=_auth_headers(456),
    )

    assert response.status_code == 403


def test_update_listing_toggles_active(client: TestClient) -> None:
    channel_id = _create_channel(client, owner_id=123, username="@ownerchannel")
    listing_id = _create_listing(client, channel_id, owner_id=123)

    response = client.put(
        f"/listings/{listing_id}",
        json={"is_active": False},
        headers=_auth_headers(123),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["is_active"] is False


def test_create_format_success(client: TestClient, db_engine) -> None:
    channel_id = _create_channel(client, owner_id=123, username="@ownerchannel")
    listing_id = _create_listing(client, channel_id, owner_id=123)

    response = client.post(
        f"/listings/{listing_id}/formats",
        json={"label": "Post", "price": "12.50"},
        headers=_auth_headers(123),
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["label"] == "Post"
    assert Decimal(payload["price"]) == Decimal("12.50")

    with Session(db_engine) as session:
        listing_format = session.exec(select(ListingFormat).where(ListingFormat.listing_id == listing_id)).one()
        assert listing_format.label == "Post"


def test_channel_listing_read_endpoint(client: TestClient, db_engine) -> None:
    channel_id = _create_channel(client, owner_id=123, username="@ownerchannel")
    listing_id = _create_listing(client, channel_id, owner_id=123)
    _create_listing_format(client, listing_id, owner_id=123)

    response = client.get(f"/channels/{channel_id}/listing", headers=_auth_headers(123))
    assert response.status_code == 200
    payload = response.json()
    assert payload["has_listing"] is True
    assert payload["listing"]["id"] == listing_id
    assert len(payload["listing"]["formats"]) == 1


def test_channel_listing_read_returns_has_listing_false(client: TestClient) -> None:
    channel_id = _create_channel(client, owner_id=123, username="@ownerchannel")

    response = client.get(f"/channels/{channel_id}/listing", headers=_auth_headers(123))
    assert response.status_code == 200
    payload = response.json()
    assert payload["has_listing"] is False


def test_create_format_duplicate_label_conflict(client: TestClient) -> None:
    channel_id = _create_channel(client, owner_id=123, username="@ownerchannel")
    listing_id = _create_listing(client, channel_id, owner_id=123)

    client.post(
        f"/listings/{listing_id}/formats",
        json={"label": "Post", "price": "12.50"},
        headers=_auth_headers(123),
    )

    response = client.post(
        f"/listings/{listing_id}/formats",
        json={"label": "Post", "price": "20.00"},
        headers=_auth_headers(123),
    )

    assert response.status_code == 409


def test_update_format_success(client: TestClient) -> None:
    channel_id = _create_channel(client, owner_id=123, username="@ownerchannel")
    listing_id = _create_listing(client, channel_id, owner_id=123)

    create_response = client.post(
        f"/listings/{listing_id}/formats",
        json={"label": "Post", "price": "12.50"},
        headers=_auth_headers(123),
    )
    format_id = create_response.json()["id"]

    response = client.put(
        f"/listings/{listing_id}/formats/{format_id}",
        json={"label": "Premium", "price": "30.00"},
        headers=_auth_headers(123),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["label"] == "Premium"
    assert Decimal(payload["price"]) == Decimal("30.00")


def test_update_format_no_fields_returns_bad_request(client: TestClient) -> None:
    channel_id = _create_channel(client, owner_id=123, username="@ownerchannel")
    listing_id = _create_listing(client, channel_id, owner_id=123)

    create_response = client.post(
        f"/listings/{listing_id}/formats",
        json={"label": "Post", "price": "12.50"},
        headers=_auth_headers(123),
    )
    format_id = create_response.json()["id"]

    response = client.put(
        f"/listings/{listing_id}/formats/{format_id}",
        json={},
        headers=_auth_headers(123),
    )

    assert response.status_code == 400


def test_non_owner_cannot_update_format(client: TestClient) -> None:
    channel_id = _create_channel(client, owner_id=123, username="@ownerchannel")
    listing_id = _create_listing(client, channel_id, owner_id=123)

    create_response = client.post(
        f"/listings/{listing_id}/formats",
        json={"label": "Post", "price": "12.50"},
        headers=_auth_headers(123),
    )
    format_id = create_response.json()["id"]

    _ensure_user(client, user_id=456)

    response = client.put(
        f"/listings/{listing_id}/formats/{format_id}",
        json={"price": "15.00"},
        headers=_auth_headers(456),
    )

    assert response.status_code == 403


def test_listing_owner_membership_enforced(client: TestClient, db_engine) -> None:
    channel_id = _create_channel(client, owner_id=123, username="@ownerchannel")

    with Session(db_engine) as session:
        owner_user = session.exec(select(User).where(User.telegram_user_id == 123)).one()
        membership = session.exec(
            select(ChannelMember)
            .where(ChannelMember.channel_id == channel_id)
            .where(ChannelMember.user_id == owner_user.id)
        ).one()
        assert membership.role == ChannelRole.owner.value
