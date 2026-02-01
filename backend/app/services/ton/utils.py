from __future__ import annotations

from decimal import Decimal, ROUND_DOWN

NANO_MULTIPLIER = Decimal("1000000000")


def ton_to_nano(amount: Decimal) -> int:
    return int((amount * NANO_MULTIPLIER).to_integral_value(rounding=ROUND_DOWN))


def nano_to_ton(amount: int | str) -> Decimal:
    return (Decimal(str(amount)) / NANO_MULTIPLIER).quantize(Decimal("0.000000001"), rounding=ROUND_DOWN)
