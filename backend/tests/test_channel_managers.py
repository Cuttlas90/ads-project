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

from app.api.deps import get_db, get_settings_dep
from app.main import app
from app.models.channel_member import ChannelMember
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


def test_add_manager_success(client: TestClient, db_engine) -> None:
    channel_id = _create_channel(client, owner_id=123, username="@ownerchannel")
    _ensure_user(client, user_id=456)

    response = client.post(
        f"/channels/{channel_id}/managers",
        json={"telegram_user_id": 456},
        headers=_auth_headers(123),
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["telegram_user_id"] == 456
    assert payload["role"] == "manager"

    with Session(db_engine) as session:
        user = session.exec(select(User).where(User.telegram_user_id == 456)).one()
        membership = session.exec(
            select(ChannelMember)
            .where(ChannelMember.channel_id == channel_id)
            .where(ChannelMember.user_id == user.id)
            .where(ChannelMember.role == ChannelRole.manager.value)
        ).one()
        assert membership is not None


def test_add_duplicate_manager_returns_conflict(client: TestClient) -> None:
    channel_id = _create_channel(client, owner_id=123, username="@ownerchannel")
    _ensure_user(client, user_id=456)

    client.post(
        f"/channels/{channel_id}/managers",
        json={"telegram_user_id": 456},
        headers=_auth_headers(123),
    )

    response = client.post(
        f"/channels/{channel_id}/managers",
        json={"telegram_user_id": 456},
        headers=_auth_headers(123),
    )

    assert response.status_code == 409


def test_add_manager_missing_user_returns_not_found(client: TestClient) -> None:
    channel_id = _create_channel(client, owner_id=123, username="@ownerchannel")

    response = client.post(
        f"/channels/{channel_id}/managers",
        json={"telegram_user_id": 999},
        headers=_auth_headers(123),
    )

    assert response.status_code == 404


def test_non_owner_cannot_add_or_remove_manager(client: TestClient) -> None:
    channel_id = _create_channel(client, owner_id=123, username="@ownerchannel")
    _ensure_user(client, user_id=456)

    response = client.post(
        f"/channels/{channel_id}/managers",
        json={"telegram_user_id": 456},
        headers=_auth_headers(456),
    )
    assert response.status_code == 403

    client.post(
        f"/channels/{channel_id}/managers",
        json={"telegram_user_id": 456},
        headers=_auth_headers(123),
    )

    response = client.delete(
        f"/channels/{channel_id}/managers/456",
        headers=_auth_headers(456),
    )

    assert response.status_code == 403


def test_remove_manager_success(client: TestClient, db_engine) -> None:
    channel_id = _create_channel(client, owner_id=123, username="@ownerchannel")
    _ensure_user(client, user_id=456)

    client.post(
        f"/channels/{channel_id}/managers",
        json={"telegram_user_id": 456},
        headers=_auth_headers(123),
    )

    response = client.delete(
        f"/channels/{channel_id}/managers/456",
        headers=_auth_headers(123),
    )

    assert response.status_code == 204

    with Session(db_engine) as session:
        membership = session.exec(
            select(ChannelMember)
            .where(ChannelMember.channel_id == channel_id)
            .where(ChannelMember.role == ChannelRole.manager.value)
        ).first()
        assert membership is None


def test_remove_manager_missing_returns_not_found(client: TestClient) -> None:
    channel_id = _create_channel(client, owner_id=123, username="@ownerchannel")
    _ensure_user(client, user_id=456)

    response = client.delete(
        f"/channels/{channel_id}/managers/456",
        headers=_auth_headers(123),
    )

    assert response.status_code == 404


def test_list_managers_owner_and_manager(client: TestClient) -> None:
    channel_id = _create_channel(client, owner_id=123, username="@ownerchannel")
    _ensure_user(client, user_id=456)

    client.post(
        f"/channels/{channel_id}/managers",
        json={"telegram_user_id": 456},
        headers=_auth_headers(123),
    )

    owner_response = client.get(
        f"/channels/{channel_id}/managers",
        headers=_auth_headers(123),
    )
    assert owner_response.status_code == 200
    owner_payload = owner_response.json()
    assert len(owner_payload) == 1
    assert owner_payload[0]["telegram_user_id"] == 456
    assert owner_payload[0]["role"] == "manager"

    manager_response = client.get(
        f"/channels/{channel_id}/managers",
        headers=_auth_headers(456),
    )
    assert manager_response.status_code == 200
    manager_payload = manager_response.json()
    assert len(manager_payload) == 1
