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
from sqlmodel import Session

from app.api.deps import get_db, get_settings_dep
from app.main import app
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


def _auth_headers(user_id: int) -> dict[str, str]:
    auth_date = str(int(time.time()))
    init_data = build_init_data({"auth_date": auth_date, "user": json.dumps({"id": user_id})})
    return {"X-Telegram-Init-Data": init_data}


def test_set_preferred_role_and_auth_me(client: TestClient) -> None:
    response = client.put(
        "/users/me/preferences",
        json={"preferred_role": "owner"},
        headers=_auth_headers(101),
    )
    assert response.status_code == 200
    assert response.json()["preferred_role"] == "owner"

    response = client.get("/auth/me", headers=_auth_headers(101))
    assert response.status_code == 200
    assert response.json()["preferred_role"] == "owner"


def test_invalid_preferred_role_rejected(client: TestClient) -> None:
    response = client.put(
        "/users/me/preferences",
        json={"preferred_role": "invalid"},
        headers=_auth_headers(101),
    )
    assert response.status_code == 400
