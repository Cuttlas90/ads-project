from __future__ import annotations

import hashlib
import hmac
import json
import time
from datetime import datetime
from urllib.parse import urlencode

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, select

from app.api.deps import get_db, get_settings_dep
from app.main import app
from app.models.user import User
from app.settings import Settings
from shared.db.base import SQLModel

BOT_TOKEN = "test-bot-token"


def build_init_data(payload: dict[str, str], bot_token: str = BOT_TOKEN) -> str:
    data = {key: str(value) for key, value in payload.items()}
    data_check_string = "\n".join(f"{key}={data[key]}" for key in sorted(data))
    secret_key = hashlib.sha256(bot_token.encode()).digest()
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


def test_auth_me_missing_init_data(client: TestClient) -> None:
    response = client.get("/auth/me")

    assert response.status_code == 401


def test_auth_me_invalid_init_data(client: TestClient) -> None:
    response = client.get("/auth/me", headers={"X-Telegram-Init-Data": "invalid"})

    assert response.status_code == 401


def test_auth_me_creates_user(client: TestClient, db_engine) -> None:
    auth_date = str(int(time.time()))
    init_data = build_init_data({"auth_date": auth_date, "user": _user_payload(123)})

    response = client.get("/auth/me", headers={"X-Telegram-Init-Data": init_data})

    assert response.status_code == 200
    assert response.json()["telegram_user_id"] == 123

    with Session(db_engine) as session:
        user = session.exec(select(User).where(User.telegram_user_id == 123)).first()
        assert user is not None
        assert user.last_login_at is not None


def test_auth_me_updates_last_login(client: TestClient, db_engine) -> None:
    auth_date = str(int(time.time()))
    init_data = build_init_data({"auth_date": auth_date, "user": _user_payload(456)})

    first_response = client.get("/auth/me", headers={"X-Telegram-Init-Data": init_data})
    assert first_response.status_code == 200

    baseline = datetime(2000, 1, 1)
    with Session(db_engine) as session:
        user = session.exec(select(User).where(User.telegram_user_id == 456)).first()
        assert user is not None
        user.last_login_at = baseline
        session.add(user)
        session.commit()

    second_response = client.get("/auth/me", headers={"X-Telegram-Init-Data": init_data})
    assert second_response.status_code == 200

    with Session(db_engine) as session:
        user = session.exec(select(User).where(User.telegram_user_id == 456)).first()
        assert user is not None
        assert user.last_login_at is not None
        assert user.last_login_at.replace(tzinfo=None) > baseline


def test_auth_me_ignores_external_user_id(client: TestClient, db_engine) -> None:
    auth_date = str(int(time.time()))
    init_data = build_init_data({"auth_date": auth_date, "user": _user_payload(789)})

    response = client.get(
        "/auth/me?telegram_user_id=999",
        headers={"X-Telegram-Init-Data": init_data},
    )

    assert response.status_code == 200
    assert response.json()["telegram_user_id"] == 789

    with Session(db_engine) as session:
        user = session.exec(select(User).where(User.telegram_user_id == 789)).first()
        assert user is not None
