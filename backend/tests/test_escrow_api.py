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
from app.models.channel import Channel
from app.models.deal import Deal, DealSourceType, DealState
from app.models.deal_escrow import DealEscrow
from app.models.listing import Listing
from app.models.listing_format import ListingFormat
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
        return Settings(
            _env_file=None,
            TELEGRAM_BOT_TOKEN=BOT_TOKEN,
            TON_ENABLED=True,
            TON_FEE_PERCENT=Decimal("5.00"),
            TON_CONFIRMATIONS_REQUIRED=3,
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


def _seed_deal(db_engine) -> int:
    with Session(db_engine) as session:
        advertiser = User(telegram_user_id=111, username="adv")
        owner = User(telegram_user_id=222, username="owner")
        session.add(advertiser)
        session.add(owner)
        session.flush()

        channel = Channel(username="channel")
        session.add(channel)
        session.flush()

        listing = Listing(channel_id=channel.id, owner_id=owner.id, is_active=True)
        session.add(listing)
        session.flush()

        listing_format = ListingFormat(listing_id=listing.id, label="Post", price=Decimal("10.00"))
        session.add(listing_format)
        session.flush()

        deal = Deal(
            source_type=DealSourceType.LISTING.value,
            advertiser_id=advertiser.id,
            channel_id=channel.id,
            channel_owner_id=owner.id,
            listing_id=listing.id,
            listing_format_id=listing_format.id,
            price_ton=Decimal("10.00"),
            ad_type=listing_format.label,
            creative_text="Hello",
            creative_media_type="image",
            creative_media_ref="ref",
            posting_params=None,
            state=DealState.ACCEPTED.value,
        )
        session.add(deal)
        session.commit()
        session.refresh(deal)
        return deal.id


def test_escrow_init_idempotent(client, db_engine, monkeypatch) -> None:
    deal_id = _seed_deal(db_engine)
    monkeypatch.setattr("app.api.routes.deals.generate_deal_deposit_address", lambda **kwargs: "EQ_TEST_ADDRESS")

    response = client.post(f"/deals/{deal_id}/escrow/init", headers=_auth_headers(111))
    assert response.status_code == 200
    payload = response.json()
    assert payload["deposit_address"] == "EQ_TEST_ADDRESS"

    response_repeat = client.post(f"/deals/{deal_id}/escrow/init", headers=_auth_headers(111))
    assert response_repeat.status_code == 200
    payload_repeat = response_repeat.json()
    assert payload_repeat["deposit_address"] == "EQ_TEST_ADDRESS"
    assert payload_repeat["escrow_id"] == payload["escrow_id"]

    with Session(db_engine) as session:
        escrows = session.exec(select(DealEscrow).where(DealEscrow.deal_id == deal_id)).all()
        assert len(escrows) == 1


def test_escrow_init_requires_advertiser(client, db_engine, monkeypatch) -> None:
    deal_id = _seed_deal(db_engine)
    monkeypatch.setattr("app.api.routes.deals.generate_deal_deposit_address", lambda **kwargs: "EQ_TEST_ADDRESS")

    response = client.post(f"/deals/{deal_id}/escrow/init", headers=_auth_headers(222))
    assert response.status_code == 403


def test_tonconnect_payload(client, db_engine, monkeypatch) -> None:
    deal_id = _seed_deal(db_engine)
    monkeypatch.setattr("app.api.routes.deals.generate_deal_deposit_address", lambda **kwargs: "EQ_TEST_ADDRESS")

    response = client.post(f"/deals/{deal_id}/escrow/init", headers=_auth_headers(111))
    assert response.status_code == 200

    response = client.post(f"/deals/{deal_id}/escrow/tonconnect-tx", headers=_auth_headers(111))
    assert response.status_code == 200
    payload = response.json()["payload"]
    assert payload["messages"][0]["address"] == "EQ_TEST_ADDRESS"
    assert payload["messages"][0]["amount"] == str(10 * 1_000_000_000)
