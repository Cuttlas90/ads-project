from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, select

from app.api.deps import get_db, get_settings_dep
from app.main import app
from app.models.user import User
from app.models.wallet_proof_challenge import WalletProofChallenge
from app.services.ton.wallet_proof import build_ton_proof_digest
from app.settings import Settings
from shared.db.base import SQLModel

BOT_TOKEN = "test-bot-token"
MANIFEST_URL = "https://app.chainofwinners.com/tonconnect-manifest.json"
PROOF_DOMAIN = "app.chainofwinners.com"
TEST_ADDRESS = "0:" + ("11" * 32)

_PRIVATE_KEY = Ed25519PrivateKey.generate()
_PUBLIC_KEY_HEX = _PRIVATE_KEY.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw).hex()


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
        return Settings(
            _env_file=None,
            TELEGRAM_BOT_TOKEN=BOT_TOKEN,
            TONCONNECT_MANIFEST_URL=MANIFEST_URL,
        )

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_settings_dep] = override_get_settings
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def _auth_headers(user_id: int) -> dict[str, str]:
    auth_date = str(int(time.time()))
    init_data = build_init_data({"auth_date": auth_date, "user": json.dumps({"id": user_id})})
    return {"X-Telegram-Init-Data": init_data}


def _issue_challenge(client: TestClient, user_id: int) -> str:
    response = client.post("/users/me/wallet/challenge", headers=_auth_headers(user_id))
    assert response.status_code == 200
    return response.json()["challenge"]


def _verify_payload(
    *,
    challenge: str,
    domain: str = PROOF_DOMAIN,
    timestamp: int | None = None,
    public_key_hex: str = _PUBLIC_KEY_HEX,
    signature_override: str | None = None,
    address: str = TEST_ADDRESS,
) -> dict[str, object]:
    ts = timestamp or int(time.time())
    digest = build_ton_proof_digest(
        address=address,
        domain_value=domain,
        timestamp=ts,
        payload=challenge,
    )
    signature = signature_override or base64.b64encode(_PRIVATE_KEY.sign(digest)).decode("ascii")
    return {
        "account": {
            "address": address,
            "chain": "-239",
            "publicKey": public_key_hex,
            "walletStateInit": "te6cckEBAQEAAgAAAA==",
        },
        "proof": {
            "timestamp": ts,
            "domain": {
                "lengthBytes": len(domain.encode("utf-8")),
                "value": domain,
            },
            "signature": signature,
            "payload": challenge,
        },
    }


def test_wallet_challenge_issued_with_five_minute_ttl(client: TestClient) -> None:
    response = client.post("/users/me/wallet/challenge", headers=_auth_headers(3001))
    assert response.status_code == 200

    payload = response.json()
    assert payload["ttl_seconds"] == 300

    expires_at = datetime.fromisoformat(payload["expires_at"].replace("Z", "+00:00"))
    now = datetime.now(timezone.utc)
    ttl_seconds = (expires_at - now).total_seconds()
    assert 250 <= ttl_seconds <= 300


def test_wallet_verify_stores_wallet_and_consumes_challenge(client: TestClient, db_engine) -> None:
    challenge = _issue_challenge(client, user_id=3002)
    response = client.post(
        "/users/me/wallet/verify",
        json=_verify_payload(challenge=challenge),
        headers=_auth_headers(3002),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["ton_wallet_address"] == TEST_ADDRESS
    assert payload["has_wallet"] is True

    with Session(db_engine) as session:
        user = session.exec(select(User).where(User.telegram_user_id == 3002)).first()
        assert user is not None
        assert user.ton_wallet_address == TEST_ADDRESS

        challenge_row = session.exec(
            select(WalletProofChallenge).where(WalletProofChallenge.challenge == challenge)
        ).first()
        assert challenge_row is not None
        assert challenge_row.consumed_at is not None


def test_wallet_verify_rejects_invalid_signature(client: TestClient, db_engine) -> None:
    challenge = _issue_challenge(client, user_id=3003)
    payload = _verify_payload(challenge=challenge)
    payload["proof"]["signature"] = "invalid-signature"

    response = client.post("/users/me/wallet/verify", json=payload, headers=_auth_headers(3003))
    assert response.status_code == 400
    assert any(token in response.json()["detail"].lower() for token in ["signature", "base64"])

    with Session(db_engine) as session:
        challenge_row = session.exec(
            select(WalletProofChallenge).where(WalletProofChallenge.challenge == challenge)
        ).first()
        assert challenge_row is not None
        assert challenge_row.consumed_at is None


def test_wallet_verify_rejects_domain_mismatch(client: TestClient) -> None:
    challenge = _issue_challenge(client, user_id=3004)
    payload = _verify_payload(challenge=challenge, domain="evil.example.com")

    response = client.post("/users/me/wallet/verify", json=payload, headers=_auth_headers(3004))
    assert response.status_code == 400
    assert "domain" in response.json()["detail"].lower()


def test_wallet_verify_rejects_replayed_challenge(client: TestClient) -> None:
    challenge = _issue_challenge(client, user_id=3005)
    payload = _verify_payload(challenge=challenge)

    first = client.post("/users/me/wallet/verify", json=payload, headers=_auth_headers(3005))
    assert first.status_code == 200

    second = client.post("/users/me/wallet/verify", json=payload, headers=_auth_headers(3005))
    assert second.status_code == 409


def test_wallet_verify_rejects_expired_challenge(client: TestClient, db_engine) -> None:
    challenge = _issue_challenge(client, user_id=3006)

    with Session(db_engine) as session:
        challenge_row = session.exec(
            select(WalletProofChallenge).where(WalletProofChallenge.challenge == challenge)
        ).first()
        assert challenge_row is not None
        challenge_row.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
        session.add(challenge_row)
        session.commit()

    response = client.post(
        "/users/me/wallet/verify",
        json=_verify_payload(challenge=challenge),
        headers=_auth_headers(3006),
    )
    assert response.status_code == 400
    assert "expired" in response.json()["detail"].lower()


def test_wallet_verify_rejects_cross_user_challenge_use(client: TestClient) -> None:
    challenge = _issue_challenge(client, user_id=3007)
    payload = _verify_payload(challenge=challenge)

    response = client.post("/users/me/wallet/verify", json=payload, headers=_auth_headers(3008))
    assert response.status_code == 403


def test_wallet_verify_requires_fresh_timestamp(client: TestClient) -> None:
    challenge = _issue_challenge(client, user_id=3009)
    stale_ts = int(time.time()) - 3600
    payload = _verify_payload(challenge=challenge, timestamp=stale_ts)

    response = client.post("/users/me/wallet/verify", json=payload, headers=_auth_headers(3009))
    assert response.status_code == 400
    assert "timestamp" in response.json()["detail"].lower()
