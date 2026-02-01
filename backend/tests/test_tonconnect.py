from __future__ import annotations

from decimal import Decimal

from app.services.ton.tonconnect import build_tonconnect_transaction
from app.settings import Settings


def test_build_tonconnect_transaction_payload() -> None:
    settings = Settings(_env_file=None, TON_ENABLED=True)
    payload = build_tonconnect_transaction(
        deposit_address="EQC_TEST_ADDRESS",
        amount_ton=Decimal("10.00"),
        settings=settings,
    )

    assert payload["messages"][0]["address"] == "EQC_TEST_ADDRESS"
    assert payload["messages"][0]["amount"] == str(10 * 1_000_000_000)
    assert payload["validUntil"] > 0
