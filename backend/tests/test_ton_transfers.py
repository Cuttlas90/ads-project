from __future__ import annotations

from decimal import Decimal

import pytest

from app.services.ton.transfers import TonTransferError, _invoke_transfer, _seqno_override_for_wallet, send_ton_transfer
from app.settings import Settings


def test_invoke_transfer_passes_seqno_when_supported() -> None:
    captured: dict[str, object] = {}

    def _transfer(destination, amount, body=None, **kwargs):  # noqa: ANN001
        captured["destination"] = destination
        captured["amount"] = amount
        captured["body"] = body
        captured.update(kwargs)
        return "hash_1"

    result = _invoke_transfer(
        _transfer,
        to_address="EQ_TEST",
        amount_ton=Decimal("0.123000000"),
        amount_nano=123,
        seqno=0,
    )

    assert result == "hash_1"
    assert captured["destination"] == "EQ_TEST"
    assert captured["amount"] == Decimal("0.123000000")
    assert captured["seqno"] == 0


def test_invoke_transfer_passes_nano_when_method_expects_nano() -> None:
    captured: dict[str, object] = {}

    def _transfer(destination, amount_nano, body=None, **kwargs):  # noqa: ANN001
        captured["destination"] = destination
        captured["amount_nano"] = amount_nano
        captured["body"] = body
        captured.update(kwargs)
        return "hash_2"

    result = _invoke_transfer(
        _transfer,
        to_address="EQ_TEST",
        amount_ton=Decimal("0.500000000"),
        amount_nano=500_000_000,
        seqno=0,
    )

    assert result == "hash_2"
    assert captured["destination"] == "EQ_TEST"
    assert captured["amount_nano"] == 500_000_000
    assert captured["seqno"] == 0


def test_seqno_override_for_wallet_uninit_account() -> None:
    class _FakeAddress:
        def to_str(self, is_user_friendly=False):  # noqa: ANN001
            assert is_user_friendly is False
            return "0:abc"

    class _FakeWallet:
        address = _FakeAddress()

    class _FakeAccount:
        class _Status:
            value = "uninit"

        status = _Status()

    class _FakeClient:
        async def get_raw_account(self, _address: str):
            return _FakeAccount()

    assert _seqno_override_for_wallet(_FakeClient(), _FakeWallet()) == 0


def test_send_ton_transfer_wraps_provider_exceptions(monkeypatch) -> None:
    class _FakeWallet:
        def transfer(self, destination, amount, body=None, **kwargs):  # noqa: ANN001
            raise RuntimeError("provider failure")

    monkeypatch.setattr("app.services.ton.transfers._toncenter_client", lambda settings: object())
    monkeypatch.setattr("app.services.ton.transfers._require_mnemonic", lambda settings: "seed words")
    monkeypatch.setattr(
        "app.services.ton.transfers.WalletV5R1.from_mnemonic",
        lambda *args, **kwargs: (_FakeWallet(), None, None, None),
    )
    monkeypatch.setattr("app.services.ton.transfers._seqno_override_for_wallet", lambda client, wallet: 0)

    settings = Settings(
        _env_file=None,
        TON_ENABLED=True,
        TON_HOT_WALLET_MNEMONIC="seed words",
        TONCENTER_API="https://testnet.toncenter.com/api/v3/jsonRPC",
    )

    with pytest.raises(TonTransferError, match="subwallet 42"):
        send_ton_transfer(
            settings=settings,
            to_address="EQ_TARGET",
            amount_ton=Decimal("0.100000000"),
            source_subwallet_id=42,
        )


def test_send_ton_transfer_passes_ton_amount_to_wallet_transfer(monkeypatch) -> None:
    captured: dict[str, object] = {}

    class _FakeWallet:
        def transfer(self, destination, amount, body=None, **kwargs):  # noqa: ANN001
            captured["destination"] = destination
            captured["amount"] = amount
            captured["body"] = body
            captured.update(kwargs)
            return "tx_ok"

    monkeypatch.setattr("app.services.ton.transfers._toncenter_client", lambda settings: object())
    monkeypatch.setattr("app.services.ton.transfers._require_mnemonic", lambda settings: "seed words")
    monkeypatch.setattr(
        "app.services.ton.transfers.WalletV5R1.from_mnemonic",
        lambda *args, **kwargs: (_FakeWallet(), None, None, None),
    )
    monkeypatch.setattr("app.services.ton.transfers._seqno_override_for_wallet", lambda client, wallet: 0)
    monkeypatch.setattr(
        "app.services.ton.transfers._validate_onchain_transfer_execution",
        lambda **kwargs: kwargs["external_hash"],
    )

    settings = Settings(
        _env_file=None,
        TON_ENABLED=True,
        TON_HOT_WALLET_MNEMONIC="seed words",
        TONCENTER_API="https://testnet.toncenter.com/api/v3/jsonRPC",
    )

    tx = send_ton_transfer(
        settings=settings,
        to_address="EQ_TARGET",
        amount_ton=Decimal("0.480000000"),
        source_subwallet_id=7,
    )

    assert tx == "tx_ok"
    assert captured["destination"] == "EQ_TARGET"
    assert captured["amount"] == Decimal("0.480000000")
    assert captured["seqno"] == 0


def test_validate_onchain_transfer_execution_raises_when_no_outgoing_message(monkeypatch) -> None:
    from app.services.ton.transfers import TonTransferError, _validate_onchain_transfer_execution

    monkeypatch.setattr(
        "app.services.ton.transfers._locate_source_tx_by_external_hash",
        lambda **kwargs: {
            "description": {
                "aborted": False,
                "action": {"msgs_created": 0, "skipped_actions": 1},
            }
        },
    )

    settings = Settings(
        _env_file=None,
        TON_ENABLED=True,
        TON_HOT_WALLET_MNEMONIC="seed words",
        TONCENTER_API="https://testnet.toncenter.com/api/v3/jsonRPC",
    )

    with pytest.raises(TonTransferError, match="produced no outgoing chain message"):
        _validate_onchain_transfer_execution(
            settings=settings,
            source_address_raw="0:abc",
            external_hash="a" * 64,
        )


def test_validate_onchain_transfer_execution_returns_chain_tx_hash_hex(monkeypatch) -> None:
    from app.services.ton.transfers import _validate_onchain_transfer_execution

    tx_hash_hex = "b" * 64
    tx_hash_b64 = "u7u7u7u7u7u7u7u7u7u7u7u7u7u7u7u7u7u7u7u7u7s="

    monkeypatch.setattr(
        "app.services.ton.transfers._locate_source_tx_by_external_hash",
        lambda **kwargs: {
            "hash": tx_hash_b64,
            "description": {
                "aborted": False,
                "action": {"msgs_created": 1, "skipped_actions": 0},
            },
        },
    )

    settings = Settings(
        _env_file=None,
        TON_ENABLED=True,
        TON_HOT_WALLET_MNEMONIC="seed words",
        TONCENTER_API="https://testnet.toncenter.com/api/v3/jsonRPC",
    )

    result = _validate_onchain_transfer_execution(
        settings=settings,
        source_address_raw="0:abc",
        external_hash="a" * 64,
    )

    assert result == tx_hash_hex
