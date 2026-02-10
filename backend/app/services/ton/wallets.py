from __future__ import annotations

from dataclasses import dataclass
import hashlib

from tonutils.client import ToncenterV3Client
from tonutils.wallet import WalletV5R1

from app.services.ton.addressing import to_raw_address
from app.services.ton.errors import TonConfigError
from app.services.ton.toncenter_url import normalize_toncenter_tonutils_base_url
from app.settings import Settings

_SUBWALLET_MODULUS = 2**31


@dataclass(frozen=True)
class DealDepositAddress:
    friendly: str
    raw: str
    subwallet_id: int
    network: str


def subwallet_id_from_deal_id(deal_id: int) -> int:
    digest = hashlib.sha256(str(deal_id).encode("utf-8")).digest()
    return int.from_bytes(digest, "big") % _SUBWALLET_MODULUS


def _require_mnemonic(settings: Settings) -> str:
    if not settings.TON_ENABLED:
        raise TonConfigError("TON integration is disabled")
    if not settings.TON_HOT_WALLET_MNEMONIC:
        raise TonConfigError("TON_HOT_WALLET_MNEMONIC is not configured")
    return settings.TON_HOT_WALLET_MNEMONIC


def _toncenter_client(settings: Settings) -> ToncenterV3Client:
    if not settings.TONCENTER_API:
        raise TonConfigError("TONCENTER_API is not configured")

    base_url = normalize_toncenter_tonutils_base_url(settings.TONCENTER_API)

    network = (settings.TON_NETWORK or "").lower()
    return ToncenterV3Client(
        api_key=settings.TONCENTER_KEY,
        is_testnet=network == "testnet",
        base_url=base_url,
        rps=1,
        max_retries=1,
    )


def resolve_deal_deposit_address(*, deal_id: int, settings: Settings) -> DealDepositAddress:
    mnemonic = _require_mnemonic(settings)
    subwallet_id = subwallet_id_from_deal_id(deal_id)
    client = _toncenter_client(settings)

    wallet, _, _, _ = WalletV5R1.from_mnemonic(client, mnemonic, subwallet_id)
    network = (settings.TON_NETWORK or "mainnet").lower()
    is_testnet = network == "testnet"
    friendly = wallet.address.to_str(
        is_user_friendly=True,
        is_url_safe=True,
        is_bounceable=False,
        is_test_only=is_testnet,
    )
    raw = to_raw_address(friendly)
    return DealDepositAddress(
        friendly=friendly,
        raw=raw,
        subwallet_id=subwallet_id,
        network=network,
    )


def generate_deal_deposit_address(*, deal_id: int, settings: Settings) -> str:
    return resolve_deal_deposit_address(deal_id=deal_id, settings=settings).friendly
