from __future__ import annotations

from app.services.ton.addressing import to_raw_address, try_to_raw_address
from app.services.ton.wallets import resolve_deal_deposit_address, subwallet_id_from_deal_id
from app.settings import Settings


MAIN_BOUNCE = "EQC3CK09jJSQNrMvUlFia7HTCUWcJ5wIFgPolR6wSbb7kl26"
MAIN_NON_BOUNCE = "UQC3CK09jJSQNrMvUlFia7HTCUWcJ5wIFgPolR6wSbb7kgB_"
TEST_BOUNCE = "kQC3CK09jJSQNrMvUlFia7HTCUWcJ5wIFgPolR6wSbb7kuYw"
TEST_NON_BOUNCE = "0QC3CK09jJSQNrMvUlFia7HTCUWcJ5wIFgPolR6wSbb7krv1"
RAW_ADDRESS = "0:b708ad3d8c949036b32f5251626bb1d309459c279c081603e8951eb049b6fb92"


def test_to_raw_address_normalizes_friendly_variants() -> None:
    expected = to_raw_address(MAIN_BOUNCE)
    assert expected == RAW_ADDRESS
    assert to_raw_address(MAIN_NON_BOUNCE) == expected
    assert to_raw_address(TEST_BOUNCE) == expected
    assert to_raw_address(TEST_NON_BOUNCE) == expected
    assert to_raw_address(RAW_ADDRESS) == expected


def test_try_to_raw_address_handles_blank_values() -> None:
    assert try_to_raw_address(None) is None
    assert try_to_raw_address("") is None
    assert try_to_raw_address("invalid") is None


def test_resolve_deal_deposit_address_applies_network_friendly_flags(monkeypatch) -> None:
    class _FakeAddress:
        def to_str(
            self,
            is_user_friendly: bool = True,
            is_url_safe: bool = True,
            is_bounceable: bool = True,
            is_test_only: bool = False,
        ) -> str:
            if not is_user_friendly:
                return RAW_ADDRESS
            if is_test_only and not is_bounceable:
                return TEST_NON_BOUNCE
            if (not is_test_only) and (not is_bounceable):
                return MAIN_NON_BOUNCE
            return MAIN_BOUNCE

    class _FakeWallet:
        address = _FakeAddress()

    monkeypatch.setattr(
        "app.services.ton.wallets.WalletV5R1.from_mnemonic",
        lambda *args, **kwargs: (_FakeWallet(), None, None, None),
    )

    settings_test = Settings(
        _env_file=None,
        TON_ENABLED=True,
        TON_NETWORK="testnet",
        TON_HOT_WALLET_MNEMONIC="seed words",
        TONCENTER_API="https://testnet.toncenter.com/api/v3/jsonRPC",
    )
    details_test = resolve_deal_deposit_address(deal_id=5, settings=settings_test)
    assert details_test.friendly == TEST_NON_BOUNCE
    assert details_test.raw == RAW_ADDRESS
    assert details_test.network == "testnet"
    assert details_test.subwallet_id == subwallet_id_from_deal_id(5)

    settings_main = Settings(
        _env_file=None,
        TON_ENABLED=True,
        TON_NETWORK="mainnet",
        TON_HOT_WALLET_MNEMONIC="seed words",
        TONCENTER_API="https://toncenter.com/api/v3/jsonRPC",
    )
    details_main = resolve_deal_deposit_address(deal_id=5, settings=settings_main)
    assert details_main.friendly == MAIN_NON_BOUNCE
    assert details_main.raw == RAW_ADDRESS
    assert details_main.network == "mainnet"
