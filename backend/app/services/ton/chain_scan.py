from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol

import httpx

from app.services.ton.errors import TonConfigError
from app.services.ton.utils import nano_to_ton
from app.settings import Settings


class TonChainAdapter(Protocol):
    def find_incoming_tx(
        self, address: str, min_amount: Decimal, since_lt: str | None
    ) -> dict | None: ...

    def get_confirmations(self, tx_hash: str) -> int: ...


@dataclass
class TonCenterAdapter:
    settings: Settings

    def _base_url(self) -> str:
        if not self.settings.TONCENTER_API:
            raise TonConfigError("TONCENTER_API is not configured")
        url = self.settings.TONCENTER_API.rstrip("/")
        if url.endswith("/jsonRPC"):
            url = url[: -len("/jsonRPC")]
        return url

    def _headers(self) -> dict[str, str]:
        if not self.settings.TONCENTER_KEY:
            return {}
        return {"X-API-Key": self.settings.TONCENTER_KEY}

    def _params(self, params: dict[str, str | int]) -> dict[str, str | int]:
        if self.settings.TONCENTER_KEY:
            params = dict(params)
            params.setdefault("api_key", self.settings.TONCENTER_KEY)
        return params

    def _get(self, path: str, *, params: dict[str, str | int] | None = None) -> dict:
        if not self.settings.TON_ENABLED:
            raise TonConfigError("TON integration is disabled")
        url = f"{self._base_url()}{path}"
        response = httpx.get(url, params=self._params(params or {}), headers=self._headers())
        if response.status_code != 200:
            raise TonConfigError(f"TonCenter error {response.status_code}: {response.text}")
        return response.json()

    def _extract_transactions(self, payload: dict) -> list[dict]:
        for key in ("transactions", "result", "data"):
            value = payload.get(key)
            if isinstance(value, list):
                return value
            if isinstance(value, dict) and isinstance(value.get("transactions"), list):
                return value["transactions"]
        if isinstance(payload.get("transactions"), dict):
            inner = payload["transactions"].get("transactions")
            if isinstance(inner, list):
                return inner
        return []

    def _extract_tx_fields(self, tx: dict) -> dict:
        tx_hash = tx.get("hash")
        lt = tx.get("lt")
        utime = tx.get("utime")
        mc_block_seqno = tx.get("mc_block_seqno")
        tx_id = tx.get("transaction_id") or {}
        if tx_hash is None:
            tx_hash = tx_id.get("hash")
        if lt is None:
            lt = tx_id.get("lt")
        if mc_block_seqno is None:
            mc_block_seqno = tx.get("block_ref", {}).get("mc_seqno")
        return {
            "hash": tx_hash,
            "lt": lt,
            "utime": utime,
            "mc_block_seqno": mc_block_seqno,
        }

    def find_incoming_tx(self, address: str, min_amount: Decimal, since_lt: str | None) -> dict | None:
        payload = self._get(
            "/transactions",
            params={"account": address, "limit": 50, "sort": "desc"},
        )
        transactions = self._extract_transactions(payload)
        candidates: list[dict] = []
        since_lt_value = int(since_lt) if since_lt is not None and str(since_lt).isdigit() else None

        for tx in transactions:
            in_msg = tx.get("in_msg") or {}
            destination = in_msg.get("destination") or in_msg.get("dest")
            if destination != address:
                continue

            value = in_msg.get("value")
            if value is None:
                continue

            amount_ton = nano_to_ton(value)
            if amount_ton < min_amount:
                continue

            fields = self._extract_tx_fields(tx)
            lt = fields.get("lt")
            if lt is None:
                continue
            lt_value = int(lt)
            if since_lt_value is not None and lt_value <= since_lt_value:
                continue

            tx_entry = dict(fields)
            tx_entry["amount_ton"] = amount_ton
            tx_entry["raw"] = tx
            candidates.append(tx_entry)

        if not candidates:
            return None

        candidates.sort(key=lambda item: int(item.get("lt")))
        return candidates[0]

    def get_confirmations(self, tx_hash: str) -> int:
        payload = self._get(
            "/transactions",
            params={"hash": tx_hash, "limit": 1},
        )
        transactions = self._extract_transactions(payload)
        if not transactions:
            return 0

        fields = self._extract_tx_fields(transactions[0])
        tx_seqno = fields.get("mc_block_seqno")
        if tx_seqno is None:
            return 0

        master_info = self._get("/masterchainInfo")
        last_seqno = None
        if isinstance(master_info.get("last"), dict):
            last_seqno = master_info["last"].get("seqno")
        if last_seqno is None:
            last_seqno = master_info.get("last_seqno")
        if last_seqno is None:
            return 0

        return max(0, int(last_seqno) - int(tx_seqno) + 1)
