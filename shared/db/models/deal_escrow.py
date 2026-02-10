from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, String, UniqueConstraint, text
from sqlmodel import Field, SQLModel


class DealEscrow(SQLModel, table=True):
    __tablename__ = "deal_escrows"
    __table_args__ = (UniqueConstraint("deal_id", name="ux_deal_escrows_deal_id"),)

    id: int | None = Field(default=None, sa_column=Column(Integer, primary_key=True))
    deal_id: int = Field(
        sa_column=Column(Integer, ForeignKey("deals.id"), nullable=False, index=True),
    )
    state: str = Field(sa_column=Column(String, nullable=False, index=True))
    deposit_address: str | None = Field(
        default=None,
        sa_column=Column(String, nullable=True, unique=True),
    )
    deposit_address_raw: str | None = Field(
        default=None,
        sa_column=Column(String, nullable=True, index=True),
    )
    subwallet_id: int = Field(sa_column=Column(Integer, nullable=False))
    escrow_network: str | None = Field(
        default=None,
        sa_column=Column(String, nullable=True),
    )
    expected_amount_ton: Decimal | None = Field(
        default=None,
        sa_column=Column(Numeric(18, 9), nullable=True),
    )
    received_amount_ton: Decimal | None = Field(
        default=None,
        sa_column=Column(Numeric(18, 9), nullable=True),
    )
    deposit_tx_hash: str | None = Field(
        default=None,
        sa_column=Column(String, nullable=True, index=True),
    )
    deposit_confirmations: int = Field(
        default=0,
        sa_column=Column(Integer, nullable=False, server_default=text("0")),
    )
    fee_percent: Decimal = Field(sa_column=Column(Numeric(5, 2), nullable=False))
    release_tx_hash: str | None = Field(
        default=None,
        sa_column=Column(String, nullable=True),
    )
    refund_tx_hash: str | None = Field(
        default=None,
        sa_column=Column(String, nullable=True),
    )
    released_amount_ton: Decimal | None = Field(
        default=None,
        sa_column=Column(Numeric(18, 9), nullable=True),
    )
    refunded_amount_ton: Decimal | None = Field(
        default=None,
        sa_column=Column(Numeric(18, 9), nullable=True),
    )
    released_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
    )
    refunded_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
    )
    created_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")),
    )
    updated_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")),
    )
