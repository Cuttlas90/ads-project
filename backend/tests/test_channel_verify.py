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
import app.services.channel_verify as channel_verify_service
from app.api.deps import get_db, get_settings_dep
from app.main import app
from app.models.channel import Channel
from app.models.channel_stats_snapshot import ChannelStatsSnapshot
from app.settings import Settings
from app.telegram.permissions import PermissionCheckResult
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


class DummyFullChat:
    def __init__(self, *, participants_count: int, id: int) -> None:
        self.participants_count = participants_count
        self.id = id


class DummyChat:
    def __init__(self, *, id: int, username: str | None, title: str | None) -> None:
        self.id = id
        self.username = username
        self.title = title


class DummyFullResponse:
    def __init__(self, *, full_chat: DummyFullChat, chats: list[DummyChat]) -> None:
        self.full_chat = full_chat
        self.chats = chats

    def to_dict(self):
        return {
            "full_chat": {
                "participants_count": self.full_chat.participants_count,
                "id": self.full_chat.id,
            },
            "chats": [
                {"id": chat.id, "username": chat.username, "title": chat.title}
                for chat in self.chats
            ],
        }


class DummyViewsPerPost:
    def __init__(self, *, current: int) -> None:
        self.current = current

    def to_dict(self):
        return {"current": self.current}


class DummyGraph:
    def __init__(self, *, data: dict[str, int]) -> None:
        self.data = data

    def to_dict(self):
        return {"data": self.data}


class DummyStatsResponse:
    def __init__(self, *, views_per_post: DummyViewsPerPost, languages_graph: DummyGraph) -> None:
        self.views_per_post = views_per_post
        self.languages_graph = languages_graph

    def to_dict(self):
        return {
            "views_per_post": self.views_per_post.to_dict(),
            "languages_graph": self.languages_graph.to_dict(),
        }


class DummyTelethonClient:
    def __init__(self, full_response: DummyFullResponse, stats_response: DummyStatsResponse) -> None:
        self._full_response = full_response
        self._stats_response = stats_response

    async def get_input_entity(self, channel):
        return channel

    async def __call__(self, request):
        name = request.__class__.__name__
        if name == "GetFullChannelRequest":
            return self._full_response
        if name == "GetBroadcastStatsRequest":
            return self._stats_response
        raise AssertionError(f"Unexpected request: {name}")


def _patch_telegram(monkeypatch, full_response: DummyFullResponse, stats_response: DummyStatsResponse):
    dummy_client = DummyTelethonClient(full_response, stats_response)

    class DummyService:
        def __init__(self, _settings) -> None:
            self._client = dummy_client

        async def connect(self) -> None:
            return None

        async def disconnect(self) -> None:
            return None

        def _get_client(self):
            return self._client

    monkeypatch.setattr(channels_route, "TelegramClientService", DummyService)
    return dummy_client


def test_verify_channel_permission_denied(client: TestClient, db_engine, monkeypatch) -> None:
    async def fake_check_bot_permissions(_client, _channel):
        return PermissionCheckResult(
            ok=False,
            is_admin=False,
            missing_permissions=["view_statistics"],
            present_permissions=[],
        )

    monkeypatch.setattr(channel_verify_service, "check_bot_permissions", fake_check_bot_permissions)

    full_response = DummyFullResponse(
        full_chat=DummyFullChat(participants_count=100, id=777),
        chats=[DummyChat(id=777, username="example", title="Example")],
    )
    stats_response = DummyStatsResponse(
        views_per_post=DummyViewsPerPost(current=50),
        languages_graph=DummyGraph(data={"en": 90}),
    )
    _patch_telegram(monkeypatch, full_response, stats_response)

    created = client.post(
        "/channels",
        json={"username": "@examplechannel"},
        headers=_auth_headers(123),
    )
    channel_id = created.json()["id"]

    response = client.post(
        f"/channels/{channel_id}/verify",
        headers=_auth_headers(123),
    )

    assert response.status_code == 403

    with Session(db_engine) as session:
        channel = session.exec(select(Channel).where(Channel.id == channel_id)).one()
        assert channel.is_verified is False
        snapshots = session.exec(
            select(ChannelStatsSnapshot).where(ChannelStatsSnapshot.channel_id == channel_id)
        ).all()
        assert len(snapshots) == 0


def test_verify_channel_success_creates_snapshot(client: TestClient, db_engine, monkeypatch) -> None:
    async def fake_check_bot_permissions(_client, _channel):
        return PermissionCheckResult(
            ok=True,
            is_admin=True,
            missing_permissions=[],
            present_permissions=["post_messages"],
        )

    monkeypatch.setattr(channel_verify_service, "check_bot_permissions", fake_check_bot_permissions)

    full_response = DummyFullResponse(
        full_chat=DummyFullChat(participants_count=111, id=999),
        chats=[DummyChat(id=999, username="UpdatedName", title="Updated Title")],
    )
    stats_response = DummyStatsResponse(
        views_per_post=DummyViewsPerPost(current=222),
        languages_graph=DummyGraph(data={"en": 80}),
    )
    _patch_telegram(monkeypatch, full_response, stats_response)

    created = client.post(
        "/channels",
        json={"username": "@examplechannel"},
        headers=_auth_headers(123),
    )
    channel_id = created.json()["id"]

    response = client.post(
        f"/channels/{channel_id}/verify",
        headers=_auth_headers(123),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["is_verified"] is True

    with Session(db_engine) as session:
        channel = session.exec(select(Channel).where(Channel.id == channel_id)).one()
        assert channel.is_verified is True
        assert channel.username == "updatedname"
        assert channel.title == "Updated Title"

        snapshots = session.exec(
            select(ChannelStatsSnapshot).where(ChannelStatsSnapshot.channel_id == channel_id)
        ).all()
        assert len(snapshots) == 1
        snapshot = snapshots[0]
        assert snapshot.subscribers == 111
        assert snapshot.avg_views == 222
        assert snapshot.raw_stats is not None


def test_verify_channel_requires_membership(client: TestClient, db_engine, monkeypatch) -> None:
    async def fake_check_bot_permissions(_client, _channel):
        return PermissionCheckResult(
            ok=True,
            is_admin=True,
            missing_permissions=[],
            present_permissions=["post_messages"],
        )

    monkeypatch.setattr(channel_verify_service, "check_bot_permissions", fake_check_bot_permissions)

    full_response = DummyFullResponse(
        full_chat=DummyFullChat(participants_count=111, id=999),
        chats=[DummyChat(id=999, username="example", title="Example")],
    )
    stats_response = DummyStatsResponse(
        views_per_post=DummyViewsPerPost(current=222),
        languages_graph=DummyGraph(data={"en": 80}),
    )
    _patch_telegram(monkeypatch, full_response, stats_response)

    created = client.post(
        "/channels",
        json={"username": "@examplechannel"},
        headers=_auth_headers(123),
    )
    channel_id = created.json()["id"]

    response = client.post(
        f"/channels/{channel_id}/verify",
        headers=_auth_headers(456),
    )

    assert response.status_code == 403

    with Session(db_engine) as session:
        snapshots = session.exec(
            select(ChannelStatsSnapshot).where(ChannelStatsSnapshot.channel_id == channel_id)
        ).all()
        assert len(snapshots) == 0
