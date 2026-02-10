"""add escrow address metadata and tx_seen uniqueness

Revision ID: e3b7f5a2c1d9
Revises: d2f1a3c4b5e6
Create Date: 2026-02-09 00:00:00.000000

"""

from __future__ import annotations

import base64
import binascii
import hashlib

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "e3b7f5a2c1d9"
down_revision = "d2f1a3c4b5e6"
branch_labels = None
depends_on = None

_SUBWALLET_MODULUS = 2**31


def _subwallet_id_from_deal_id(deal_id: int) -> int:
    digest = hashlib.sha256(str(deal_id).encode("utf-8")).digest()
    return int.from_bytes(digest, "big") % _SUBWALLET_MODULUS


def _decode_friendly_address(value: str) -> tuple[int, bytes, int] | None:
    normalized = value.strip()
    if not normalized:
        return None

    padding = "=" * (-len(normalized) % 4)
    candidate = normalized + padding

    try:
        decoded = base64.b64decode(candidate, validate=True)
    except binascii.Error:
        try:
            decoded = base64.urlsafe_b64decode(candidate)
        except binascii.Error:
            return None

    if len(decoded) != 36:
        return None

    body = decoded[:34]
    checksum = decoded[34:]
    if _crc16_xmodem(body) != checksum:
        return None

    flags = body[0]
    workchain_byte = body[1]
    workchain = workchain_byte if workchain_byte < 128 else workchain_byte - 256
    address_hash = body[2:34]
    return workchain, address_hash, flags


def _normalize_raw_address(value: str | None) -> str | None:
    if value is None:
        return None

    candidate = value.strip()
    if not candidate:
        return None

    if ":" in candidate:
        parts = candidate.split(":", 1)
        if len(parts) != 2:
            return None
        workchain_text, hash_text = parts
        try:
            workchain = int(workchain_text)
            address_hash = bytes.fromhex(hash_text)
        except ValueError:
            return None
        if len(address_hash) != 32:
            return None
        return f"{workchain}:{address_hash.hex()}"

    decoded = _decode_friendly_address(candidate)
    if decoded is None:
        return None
    workchain, address_hash, _ = decoded
    return f"{workchain}:{address_hash.hex()}"


def _infer_network(value: str | None) -> str | None:
    if value is None or ":" in value:
        return None
    decoded = _decode_friendly_address(value)
    if decoded is None:
        return None
    _, _, flags = decoded
    return "testnet" if (flags & 0x80) else "mainnet"


def _crc16_xmodem(data: bytes) -> bytes:
    crc = 0
    for item in data:
        crc ^= item << 8
        for _ in range(8):
            if crc & 0x8000:
                crc = ((crc << 1) ^ 0x1021) & 0xFFFF
            else:
                crc = (crc << 1) & 0xFFFF
    return crc.to_bytes(2, "big")


def upgrade() -> None:
    op.add_column("deal_escrows", sa.Column("deposit_address_raw", sa.String(), nullable=True))
    op.add_column("deal_escrows", sa.Column("subwallet_id", sa.Integer(), nullable=True))
    op.add_column("deal_escrows", sa.Column("escrow_network", sa.String(), nullable=True))
    op.create_index("ix_deal_escrows_deposit_address_raw", "deal_escrows", ["deposit_address_raw"], unique=False)

    bind = op.get_bind()
    rows = bind.execute(sa.text("SELECT id, deal_id, deposit_address FROM deal_escrows")).mappings().all()
    for row in rows:
        escrow_id = int(row["id"])
        deal_id = int(row["deal_id"])
        deposit_address = row.get("deposit_address")
        bind.execute(
            sa.text(
                """
                UPDATE deal_escrows
                SET subwallet_id = :subwallet_id,
                    deposit_address_raw = COALESCE(:deposit_address_raw, deposit_address_raw),
                    escrow_network = COALESCE(:escrow_network, escrow_network)
                WHERE id = :escrow_id
                """
            ),
            {
                "escrow_id": escrow_id,
                "subwallet_id": _subwallet_id_from_deal_id(deal_id),
                "deposit_address_raw": _normalize_raw_address(deposit_address),
                "escrow_network": _infer_network(deposit_address),
            },
        )

    op.alter_column("deal_escrows", "subwallet_id", nullable=False)

    # Guarantee idempotent tx_seen ingestion by escrow/tx identity.
    op.execute(
        """
        CREATE UNIQUE INDEX ux_escrow_events_tx_seen_hash
        ON escrow_events (escrow_id, (payload ->> 'tx_hash'))
        WHERE event_type = 'tx_seen' AND (payload ->> 'tx_hash') IS NOT NULL
        """
    )
    op.execute(
        """
        CREATE UNIQUE INDEX ux_escrow_events_tx_seen_lt
        ON escrow_events (escrow_id, (payload ->> 'lt'))
        WHERE event_type = 'tx_seen' AND (payload ->> 'lt') IS NOT NULL
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ux_escrow_events_tx_seen_lt")
    op.execute("DROP INDEX IF EXISTS ux_escrow_events_tx_seen_hash")

    op.drop_index("ix_deal_escrows_deposit_address_raw", table_name="deal_escrows")
    op.drop_column("deal_escrows", "escrow_network")
    op.drop_column("deal_escrows", "subwallet_id")
    op.drop_column("deal_escrows", "deposit_address_raw")
