from __future__ import annotations

import asyncio
import inspect
from decimal import Decimal

from tonutils.client import ToncenterV3Client
from tonutils.wallet import WalletV5R1

from app.services.ton.errors import TonConfigError
from app.services.ton.utils import ton_to_nano
from app.settings import Settings


class TonTransferError(RuntimeError):
    pass


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


def _invoke_transfer(method, *, to_address: str, amount_nano: int):
    signature = inspect.signature(method)
    kwargs = {}
    for name in signature.parameters:
        if name in {"destination", "dest", "to_addr", "to_address", "address"}:
            kwargs[name] = to_address
        elif name in {"amount", "amount_nano", "value", "nano"}:
            kwargs[name] = amount_nano
        elif name in {"comment", "payload", "message", "body", "memo"}:
            kwargs[name] = None
        elif name in {"bounce"}:
            kwargs[name] = False
    result = method(**kwargs)
    if inspect.isawaitable(result):
        try:
            result = asyncio.run(result)
        except RuntimeError:
            loop = asyncio.new_event_loop()
            try:
                result = loop.run_until_complete(result)
            finally:
                loop.close()
    return result


def _extract_tx_hash(result) -> str:
    if isinstance(result, str):
        return result
    if isinstance(result, dict):
        for key in ("hash", "tx_hash", "transaction_hash"):
            value = result.get(key)
            if value:
                return str(value)
    raise TonTransferError("Transfer did not return transaction hash")


def send_ton_transfer(*, settings: Settings, to_address: str, amount_ton: Decimal) -> str:
    mnemonic = _require_mnemonic(settings)
    client = _toncenter_client(settings)

    wallet, _, _, _ = WalletV5R1.from_mnemonic(client, mnemonic, 0)
    amount_nano = ton_to_nano(amount_ton)

    for method_name in ("transfer", "send_transfer", "send", "send_transaction"):
        method = getattr(wallet, method_name, None)
        if method is None:
            continue
        result = _invoke_transfer(method, to_address=to_address, amount_nano=amount_nano)
        return _extract_tx_hash(result)

    raise TonTransferError("No compatible transfer method found on WalletV5R1")
