from __future__ import annotations

from app.services.ton.toncenter_url import (
    normalize_toncenter_tonutils_base_url,
    normalize_toncenter_v3_base_url,
)


def test_normalize_toncenter_v3_base_url_from_root() -> None:
    assert (
        normalize_toncenter_v3_base_url("https://testnet.toncenter.com")
        == "https://testnet.toncenter.com/api/v3"
    )


def test_normalize_toncenter_v3_base_url_from_jsonrpc() -> None:
    assert (
        normalize_toncenter_v3_base_url("https://testnet.toncenter.com/api/v3/jsonRPC")
        == "https://testnet.toncenter.com/api/v3"
    )


def test_normalize_toncenter_tonutils_base_url_strips_api_v3_path() -> None:
    assert (
        normalize_toncenter_tonutils_base_url("https://testnet.toncenter.com/api/v3/jsonRPC")
        == "https://testnet.toncenter.com"
    )
    assert (
        normalize_toncenter_tonutils_base_url("https://testnet.toncenter.com/api/v3")
        == "https://testnet.toncenter.com"
    )
