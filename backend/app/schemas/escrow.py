from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel


class EscrowInitResponse(BaseModel):
    escrow_id: int
    deal_id: int
    state: str
    deposit_address: str
    fee_percent: Decimal
    confirmations_required: int


class TonConnectTxResponse(BaseModel):
    escrow_id: int
    deal_id: int
    payload: dict
