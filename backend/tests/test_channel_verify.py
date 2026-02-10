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
from app.domain.channel_verification import ChannelVerificationError
from app.main import app
from app.models.channel import Channel
from app.models.channel_stats_snapshot import ChannelStatsSnapshot
from app.settings import Settings
from app.telegram.permissions import PermissionCheckResult
from shared.db.base import SQLModel
from shared.telegram.errors import TelegramAuthorizationError

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


class DummyStatsPercentValue:
    def __init__(self, *, part: float, total: float) -> None:
        self.part = part
        self.total = total

    def to_dict(self):
        return {"_": "StatsPercentValue", "part": self.part, "total": self.total}


class DummyStatsResponse:
    def __init__(self, *, views_per_post: DummyViewsPerPost, languages_graph: DummyGraph) -> None:
        self.views_per_post = views_per_post
        self.languages_graph = languages_graph

    def to_dict(self):
        return {
            "views_per_post": self.views_per_post.to_dict(),
            "languages_graph": self.languages_graph.to_dict(),
        }


class DummyBoostsStatusResponse:
    def __init__(self, *, premium_audience: DummyStatsPercentValue | None = None) -> None:
        self.premium_audience = premium_audience

    def to_dict(self):
        return {
            "_": "BoostsStatus",
            "premium_audience": (
                self.premium_audience.to_dict() if self.premium_audience is not None else None
            ),
        }


class DummyTelethonClient:
    def __init__(
        self,
        full_response: DummyFullResponse,
        stats_response: DummyStatsResponse,
        boosts_status: DummyBoostsStatusResponse | None = None,
        *,
        authorized: bool = True,
        boosts_error: Exception | None = None,
    ) -> None:
        self._full_response = full_response
        self._stats_response = stats_response
        self._boosts_status = boosts_status
        self._authorized = authorized
        self._boosts_error = boosts_error

    async def get_input_entity(self, channel):
        return channel

    async def is_user_authorized(self) -> bool:
        return self._authorized

    async def __call__(self, request):
        name = request.__class__.__name__
        if name == "GetFullChannelRequest":
            return self._full_response
        if name == "GetBroadcastStatsRequest":
            return self._stats_response
        if name == "GetBoostsStatusRequest":
            if self._boosts_error is not None:
                raise self._boosts_error
            return self._boosts_status
        raise AssertionError(f"Unexpected request: {name}")


def _patch_telegram(
    monkeypatch,
    full_response: DummyFullResponse,
    stats_response: DummyStatsResponse,
    boosts_status: DummyBoostsStatusResponse | None = None,
    *,
    authorized: bool = True,
    connect_error: Exception | None = None,
    boosts_error: Exception | None = None,
):
    dummy_client = DummyTelethonClient(
        full_response,
        stats_response,
        boosts_status,
        authorized=authorized,
        boosts_error=boosts_error,
    )

    class DummyService:
        def __init__(self, _settings) -> None:
            self._client = dummy_client

        async def connect(self) -> None:
            if connect_error is not None:
                raise connect_error
            return None

        async def require_authorized(self) -> None:
            if not await self._client.is_user_authorized():
                raise TelegramAuthorizationError(
                    "Telegram client session is not authorized. Authenticate TELEGRAM_SESSION_NAME first."
                )

        async def disconnect(self) -> None:
            return None

        def client(self):
            return self._client

        def _get_client(self):
            return self._client

    monkeypatch.setattr(channels_route, "TelegramClientService", DummyService)
    return dummy_client


def test_verify_channel_permission_denied(client: TestClient, db_engine, monkeypatch) -> None:
    async def fake_check_bot_permissions(_bot_api, _channel):
        return PermissionCheckResult(
            ok=False,
            is_admin=False,
            missing_permissions=["can_edit_messages"],
            present_permissions=[],
            permission_details={"can_post_messages": True, "can_edit_messages": False},
            raw_member={"status": "administrator"},
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
    async def fake_check_bot_permissions(_bot_api, _channel):
        return PermissionCheckResult(
            ok=True,
            is_admin=True,
            missing_permissions=[],
            present_permissions=["can_edit_messages", "can_post_messages"],
            permission_details={
                "can_post_messages": True,
                "can_edit_messages": True,
                "can_manage_chat": True,
            },
            raw_member={
                "status": "administrator",
                "can_post_messages": True,
                "can_edit_messages": True,
                "can_manage_chat": True,
            },
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
        assert channel.telegram_channel_id == -1000000000999
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
        assert snapshot.raw_stats["bot_chat_member"]["status"] == "administrator"
        assert snapshot.raw_stats["bot_permission_details"]["can_post_messages"] is True


def test_verify_channel_derives_premium_ratio_from_boosts_status(
    client: TestClient, db_engine, monkeypatch
) -> None:
    async def fake_check_bot_permissions(_bot_api, _channel):
        return PermissionCheckResult(
            ok=True,
            is_admin=True,
            missing_permissions=[],
            present_permissions=["can_edit_messages", "can_post_messages"],
            permission_details={
                "can_post_messages": True,
                "can_edit_messages": True,
                "can_manage_chat": True,
            },
            raw_member={
                "status": "administrator",
                "can_post_messages": True,
                "can_edit_messages": True,
                "can_manage_chat": True,
            },
        )

    monkeypatch.setattr(channel_verify_service, "check_bot_permissions", fake_check_bot_permissions)

    full_response = DummyFullResponse(
        full_chat=DummyFullChat(participants_count=4511, id=999),
        chats=[DummyChat(id=999, username="premiumexample", title="Premium Example")],
    )
    stats_response = DummyStatsResponse(
        views_per_post=DummyViewsPerPost(current=1740),
        languages_graph=DummyGraph(data={"en": 80}),
    )
    boosts_status = DummyBoostsStatusResponse(
        premium_audience=DummyStatsPercentValue(part=56.0, total=4511.0)
    )
    _patch_telegram(
        monkeypatch,
        full_response,
        stats_response,
        boosts_status,
    )

    created = client.post(
        "/channels",
        json={"username": "@premiumexamplechannel"},
        headers=_auth_headers(123),
    )
    channel_id = created.json()["id"]

    response = client.post(
        f"/channels/{channel_id}/verify",
        headers=_auth_headers(123),
    )

    assert response.status_code == 200

    with Session(db_engine) as session:
        snapshot = session.exec(
            select(ChannelStatsSnapshot).where(ChannelStatsSnapshot.channel_id == channel_id)
        ).one()
        assert isinstance(snapshot.premium_stats, dict)
        assert snapshot.premium_stats["premium_ratio"] == pytest.approx(56.0 / 4511.0)
        assert snapshot.premium_stats["premium_audience"]["part"] == 56.0
        assert snapshot.premium_stats["premium_audience"]["total"] == 4511.0
        assert snapshot.raw_stats is not None
        assert snapshot.raw_stats["boosts_status"]["_"] == "BoostsStatus"


def test_verify_channel_boosts_failure_is_non_blocking(client: TestClient, db_engine, monkeypatch) -> None:
    async def fake_check_bot_permissions(_bot_api, _channel):
        return PermissionCheckResult(
            ok=True,
            is_admin=True,
            missing_permissions=[],
            present_permissions=["can_edit_messages", "can_post_messages"],
            permission_details={
                "can_post_messages": True,
                "can_edit_messages": True,
                "can_manage_chat": True,
            },
            raw_member={
                "status": "administrator",
                "can_post_messages": True,
                "can_edit_messages": True,
                "can_manage_chat": True,
            },
        )

    monkeypatch.setattr(channel_verify_service, "check_bot_permissions", fake_check_bot_permissions)

    full_response = DummyFullResponse(
        full_chat=DummyFullChat(participants_count=3200, id=888),
        chats=[DummyChat(id=888, username="boostsfailure", title="Boosts Failure")],
    )
    stats_response = DummyStatsResponse(
        views_per_post=DummyViewsPerPost(current=1400),
        languages_graph=DummyGraph(data={"en": 80}),
    )
    _patch_telegram(
        monkeypatch,
        full_response,
        stats_response,
        boosts_error=RuntimeError("boosts unavailable"),
    )

    created = client.post(
        "/channels",
        json={"username": "@boostsfailurechannel"},
        headers=_auth_headers(123),
    )
    channel_id = created.json()["id"]

    response = client.post(
        f"/channels/{channel_id}/verify",
        headers=_auth_headers(123),
    )

    assert response.status_code == 200

    with Session(db_engine) as session:
        snapshot = session.exec(
            select(ChannelStatsSnapshot).where(ChannelStatsSnapshot.channel_id == channel_id)
        ).one()
        assert snapshot.raw_stats is not None
        assert snapshot.raw_stats["boosts_status"] is None


def test_verify_channel_serializes_bytes_in_raw_stats(client: TestClient, db_engine, monkeypatch) -> None:
    async def fake_check_bot_permissions(_bot_api, _channel):
        return PermissionCheckResult(
            ok=True,
            is_admin=True,
            missing_permissions=[],
            present_permissions=["can_edit_messages", "can_post_messages"],
            permission_details={
                "can_post_messages": True,
                "can_edit_messages": True,
                "can_manage_chat": True,
            },
            raw_member={
                "status": "administrator",
                "can_post_messages": True,
                "can_edit_messages": True,
            },
        )

    monkeypatch.setattr(channel_verify_service, "check_bot_permissions", fake_check_bot_permissions)

    class DummyFullResponseWithBytes(DummyFullResponse):
        def to_dict(self):
            payload = super().to_dict()
            payload["raw_bin"] = b"\xff\x00"
            return payload

    class DummyStatsResponseWithBytes(DummyStatsResponse):
        def to_dict(self):
            payload = super().to_dict()
            payload["blob"] = b"abc"
            return payload

    full_response = DummyFullResponseWithBytes(
        full_chat=DummyFullChat(participants_count=111, id=999),
        chats=[DummyChat(id=999, username="UpdatedName", title="Updated Title")],
    )
    stats_response = DummyStatsResponseWithBytes(
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

    def has_bytes(value) -> bool:
        if isinstance(value, (bytes, bytearray, memoryview)):
            return True
        if isinstance(value, dict):
            return any(has_bytes(v) for v in value.values())
        if isinstance(value, (list, tuple, set)):
            return any(has_bytes(v) for v in value)
        return False

    with Session(db_engine) as session:
        snapshot = session.exec(
            select(ChannelStatsSnapshot).where(ChannelStatsSnapshot.channel_id == channel_id)
        ).one()
        assert snapshot.raw_stats is not None
        assert has_bytes(snapshot.raw_stats) is False
        assert snapshot.raw_stats["full_channel"]["raw_bin"] == {"__bytes_b64__": "/wA="}
        assert snapshot.raw_stats["statistics"]["blob"] == "abc"


def test_verify_channel_requires_membership(client: TestClient, db_engine, monkeypatch) -> None:
    async def fake_check_bot_permissions(_bot_api, _channel):
        return PermissionCheckResult(
            ok=True,
            is_admin=True,
            missing_permissions=[],
            present_permissions=["can_post_messages", "can_edit_messages"],
            permission_details={"can_post_messages": True, "can_edit_messages": True},
            raw_member={"status": "administrator"},
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


def test_verify_channel_telegram_failure_returns_502(client: TestClient, monkeypatch) -> None:
    async def fake_verify_channel(**kwargs):
        raise ChannelVerificationError(
            "Failed to verify channel with Telegram",
            channel_id=1,
        )

    monkeypatch.setattr(channels_route, "verify_channel", fake_verify_channel)

    response = client.post(
        "/channels/1/verify",
        headers=_auth_headers(123),
    )

    assert response.status_code == 502
    assert "Failed to verify channel with Telegram" in response.json()["detail"]


def test_verify_channel_unauthorized_telethon_session_returns_502(
    client: TestClient, monkeypatch
) -> None:
    async def fake_check_bot_permissions(_bot_api, _channel):
        return PermissionCheckResult(
            ok=True,
            is_admin=True,
            missing_permissions=[],
            present_permissions=["can_edit_messages", "can_post_messages"],
            permission_details={"can_post_messages": True, "can_edit_messages": True},
            raw_member={"status": "administrator"},
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
    _patch_telegram(monkeypatch, full_response, stats_response, authorized=False)

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

    assert response.status_code == 502
    assert "not authorized" in response.json()["detail"].lower()


def test_verify_channel_connect_failure_has_no_partial_persistence(
    client: TestClient, db_engine, monkeypatch
) -> None:
    async def fake_check_bot_permissions(_bot_api, _channel):
        return PermissionCheckResult(
            ok=True,
            is_admin=True,
            missing_permissions=[],
            present_permissions=["can_edit_messages", "can_post_messages"],
            permission_details={"can_post_messages": True, "can_edit_messages": True},
            raw_member={"status": "administrator"},
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
    _patch_telegram(
        monkeypatch,
        full_response,
        stats_response,
        connect_error=RuntimeError("mtproto down"),
    )

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

    assert response.status_code == 502

    with Session(db_engine) as session:
        channel = session.exec(select(Channel).where(Channel.id == channel_id)).one()
        assert channel.is_verified is False
        snapshots = session.exec(
            select(ChannelStatsSnapshot).where(ChannelStatsSnapshot.channel_id == channel_id)
        ).all()
        assert len(snapshots) == 0
