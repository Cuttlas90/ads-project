from __future__ import annotations

import asyncio
import base64
import inspect
import time
from decimal import Decimal

import httpx
from tonutils.client import ToncenterV3Client
from tonutils.wallet import WalletV5R1

from app.services.ton.errors import TonConfigError
from app.services.ton.toncenter_url import normalize_toncenter_tonutils_base_url, normalize_toncenter_v3_base_url
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


def _invoke_transfer(
    method,
    *,
    to_address: str,
    amount_ton: Decimal,
    amount_nano: int,
    seqno: int | None = None,
):
    signature = inspect.signature(method)
    accepts_var_kwargs = any(
        parameter.kind == inspect.Parameter.VAR_KEYWORD for parameter in signature.parameters.values()
    )
    kwargs = {}
    for name in signature.parameters:
        if name in {"destination", "dest", "to_addr", "to_address", "address"}:
            kwargs[name] = to_address
        elif name in {"amount", "value"}:
            kwargs[name] = amount_ton
        elif name in {"amount_nano", "nano", "value_nano"}:
            kwargs[name] = amount_nano
        elif name in {"comment", "payload", "message", "body", "memo"}:
            kwargs[name] = None
        elif name in {"bounce"}:
            kwargs[name] = False
    if seqno is not None and ("seqno" in signature.parameters or accepts_var_kwargs):
        kwargs["seqno"] = seqno
    result = method(**kwargs)
    if inspect.isawaitable(result):
        result = _run_async(result)
    return result


def _run_async(coro):
    try:
        return asyncio.run(coro)
    except RuntimeError:
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()


def _seqno_override_for_wallet(client: ToncenterV3Client, wallet) -> int | None:
    async def _resolve_status():
        account = await client.get_raw_account(wallet.address.to_str(is_user_friendly=False))
        status = getattr(account, "status", None)
        return str(getattr(status, "value", status)).lower()

    try:
        status = _run_async(_resolve_status())
    except Exception:
        return None

    if status in {"uninit", "nonexist"}:
        return 0
    return None


def _extract_tx_hash(result) -> str:
    if isinstance(result, str):
        return result
    if isinstance(result, dict):
        for key in ("hash", "tx_hash", "transaction_hash"):
            value = result.get(key)
            if value:
                return str(value)
    raise TonTransferError("Transfer did not return transaction hash")


def _hash_hex_to_base64(value: str) -> str | None:
    candidate = value.strip()
    if not candidate:
        return None
    try:
        raw = bytes.fromhex(candidate)
    except ValueError:
        return None
    if len(raw) != 32:
        return None
    return base64.b64encode(raw).decode()


def _hash_base64_to_hex(value: str) -> str | None:
    candidate = value.strip()
    if not candidate:
        return None
    try:
        raw = base64.b64decode(candidate, validate=True)
    except Exception:
        return None
    if len(raw) != 32:
        return None
    return raw.hex()


def _toncenter_v3_headers(settings: Settings) -> dict[str, str]:
    if not settings.TONCENTER_KEY:
        return {}
    return {"X-API-Key": settings.TONCENTER_KEY}


def _toncenter_v3_params(settings: Settings, params: dict[str, str | int]) -> dict[str, str | int]:
    if not settings.TONCENTER_KEY:
        return params
    with_key = dict(params)
    with_key.setdefault("api_key", settings.TONCENTER_KEY)
    return with_key


def _locate_source_tx_by_external_hash(
    *,
    settings: Settings,
    source_address_raw: str,
    external_hash: str,
    attempts: int = 6,
    poll_interval_seconds: float = 1.0,
) -> dict | None:
    if not settings.TONCENTER_API:
        return None

    target_hash = _hash_hex_to_base64(external_hash) or external_hash
    url = f"{normalize_toncenter_v3_base_url(settings.TONCENTER_API)}/transactions"
    params = _toncenter_v3_params(
        settings,
        {"account": source_address_raw, "limit": 20, "sort": "desc"},
    )

    for attempt in range(attempts):
        response = httpx.get(
            url,
            params=params,
            headers=_toncenter_v3_headers(settings),
            timeout=10,
        )
        if response.status_code != 200:
            break
        payload = response.json()
        transactions = payload.get("transactions") if isinstance(payload, dict) else None
        if isinstance(transactions, list):
            for tx in transactions:
                in_msg = tx.get("in_msg") if isinstance(tx, dict) else None
                if not isinstance(in_msg, dict):
                    continue
                if in_msg.get("hash_norm") == target_hash:
                    return tx
        if attempt + 1 < attempts:
            time.sleep(poll_interval_seconds)
    return None


def _validate_onchain_transfer_execution(
    *,
    settings: Settings,
    source_address_raw: str,
    external_hash: str,
) -> str:
    tx = _locate_source_tx_by_external_hash(
        settings=settings,
        source_address_raw=source_address_raw,
        external_hash=external_hash,
    )
    if tx is None:
        return external_hash

    description = tx.get("description") if isinstance(tx, dict) else None
    if not isinstance(description, dict):
        return external_hash
    action = description.get("action") if isinstance(description.get("action"), dict) else {}
    aborted = bool(description.get("aborted"))
    msgs_created_raw = action.get("msgs_created", 0)
    skipped_raw = action.get("skipped_actions", 0)
    try:
        msgs_created = int(msgs_created_raw)
    except (TypeError, ValueError):
        msgs_created = 0
    try:
        skipped_actions = int(skipped_raw)
    except (TypeError, ValueError):
        skipped_actions = 0

    if aborted or msgs_created <= 0:
        raise TonTransferError(
            "TON transfer was accepted but produced no outgoing chain message "
            f"(aborted={aborted}, msgs_created={msgs_created}, skipped_actions={skipped_actions})"
        )

    tx_hash_raw = tx.get("hash")
    if isinstance(tx_hash_raw, str):
        return _hash_base64_to_hex(tx_hash_raw) or tx_hash_raw
    return external_hash


def send_ton_transfer(
    *,
    settings: Settings,
    to_address: str,
    amount_ton: Decimal,
    source_subwallet_id: int = 0,
) -> str:
    mnemonic = _require_mnemonic(settings)
    if source_subwallet_id < 0:
        raise TonTransferError("source_subwallet_id must be non-negative")
    client = _toncenter_client(settings)

    wallet, _, _, _ = WalletV5R1.from_mnemonic(client, mnemonic, source_subwallet_id)
    amount_nano = ton_to_nano(amount_ton)
    seqno_override = _seqno_override_for_wallet(client, wallet)

    for method_name in ("transfer", "send_transfer", "send", "send_transaction"):
        method = getattr(wallet, method_name, None)
        if method is None:
            continue
        try:
            result = _invoke_transfer(
                method,
                to_address=to_address,
                amount_ton=amount_ton,
                amount_nano=amount_nano,
                seqno=seqno_override,
            )
        except Exception as exc:  # pragma: no cover - provider/network/runtime failures
            raise TonTransferError(
                f"TON transfer failed for subwallet {source_subwallet_id}: {exc}"
            ) from exc
        external_hash = _extract_tx_hash(result)
        source_address_raw = wallet.address.to_str(is_user_friendly=False)
        return _validate_onchain_transfer_execution(
            settings=settings,
            source_address_raw=source_address_raw,
            external_hash=external_hash,
        )

    raise TonTransferError("No compatible transfer method found on WalletV5R1")
