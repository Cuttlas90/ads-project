from __future__ import annotations

from decimal import Decimal

import pytest
from fastapi import HTTPException

from app.api.routes.marketplace import _parse_decimal, _parse_float, _parse_int, _validate_range


def test_parse_int_valid() -> None:
    assert _parse_int("5", field="page", minimum=1) == 5


def test_parse_int_invalid_raises() -> None:
    with pytest.raises(HTTPException):
        _parse_int("bad", field="page", minimum=1)


def test_parse_decimal_valid() -> None:
    assert _parse_decimal("10.50", field="min_price", minimum=Decimal("0")) == Decimal("10.50")


def test_parse_decimal_invalid_raises() -> None:
    with pytest.raises(HTTPException):
        _parse_decimal("bad", field="min_price", minimum=Decimal("0"))


def test_parse_float_valid() -> None:
    assert _parse_float("0.25", field="min_premium_pct", minimum=0.0) == 0.25


def test_parse_float_invalid_raises() -> None:
    with pytest.raises(HTTPException):
        _parse_float("bad", field="min_premium_pct", minimum=0.0)


def test_validate_range_invalid() -> None:
    with pytest.raises(HTTPException):
        _validate_range(10, 5, field="price")
