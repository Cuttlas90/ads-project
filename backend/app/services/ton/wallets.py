from __future__ import annotations

import hashlib

from tonutils.client import ToncenterV3Client
from tonutils.wallet import WalletV5R1

from app.services.ton.errors import TonConfigError
from app.settings import Settings

_SUBWALLET_MODULUS = 2**31


def _subwallet_id_from_deal_id(deal_id: int) -> int:
    digest = hashlib.sha256(str(deal_id).encode("utf-8")).digest()
    return int.from_bytes(digest, "big") % _SUBWALLET_MODULUS


def _require_mnemonic(settings: Settings) -> str:
    if not settings.TON_ENABLED:
        raise TonConfigError("TON integration is disabled")
    if not settings.TON_HOT_WALLET_MNEMONIC:
        raise TonConfigError("TON_HOT_WALLET_MNEMONIC is not configured")
    return settings.TON_HOT_WALLET_MNEMONIC


def _toncenter_client(settings: Settings) -> ToncenterV3Client:
    network = (settings.TON_NETWORK or "").lower()
    return ToncenterV3Client(
        api_key=settings.TONCENTER_KEY,
        is_testnet=network == "testnet",
        rps=1,
        max_retries=1,
    )


def generate_deal_deposit_address(*, deal_id: int, settings: Settings) -> str:
    mnemonic = _require_mnemonic(settings)
    subwallet_id = _subwallet_id_from_deal_id(deal_id)
    client = _toncenter_client(settings)

    wallet, _, _, _ = WalletV5R1.from_mnemonic(client, mnemonic, subwallet_id)
    return wallet.address.to_str()
