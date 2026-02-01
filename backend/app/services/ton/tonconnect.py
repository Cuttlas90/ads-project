from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal

from app.services.ton.errors import TonConfigError
from app.services.ton.utils import ton_to_nano
from app.settings import Settings


def build_tonconnect_transaction(
    *,
    deposit_address: str,
    amount_ton: Decimal,
    settings: Settings,
    valid_for_seconds: int = 600,
) -> dict:
    if not settings.TON_ENABLED:
        raise TonConfigError("TON integration is disabled")
    if not deposit_address:
        raise TonConfigError("Deposit address is missing")

    valid_until = int((datetime.now(timezone.utc) + timedelta(seconds=valid_for_seconds)).timestamp())
    return {
        "validUntil": valid_until,
        "messages": [
            {
                "address": deposit_address,
                "amount": str(ton_to_nano(amount_ton)),
            }
        ],
    }
