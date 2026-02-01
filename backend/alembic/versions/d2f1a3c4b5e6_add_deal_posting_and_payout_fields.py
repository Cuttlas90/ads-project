"""add deal posting and payout fields

Revision ID: d2f1a3c4b5e6
Revises: f6a2d8c1b3e4
Create Date: 2026-02-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "d2f1a3c4b5e6"
down_revision = "f6a2d8c1b3e4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("deals", sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("deals", sa.Column("verification_window_hours", sa.Integer(), nullable=True))
    op.add_column("deals", sa.Column("posted_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("deals", sa.Column("posted_message_id", sa.String(), nullable=True))
    op.add_column("deals", sa.Column("posted_content_hash", sa.String(), nullable=True))
    op.add_column("deals", sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True))

    op.add_column("deal_escrows", sa.Column("release_tx_hash", sa.String(), nullable=True))
    op.add_column("deal_escrows", sa.Column("refund_tx_hash", sa.String(), nullable=True))
    op.add_column("deal_escrows", sa.Column("released_amount_ton", sa.Numeric(18, 9), nullable=True))
    op.add_column("deal_escrows", sa.Column("refunded_amount_ton", sa.Numeric(18, 9), nullable=True))
    op.add_column("deal_escrows", sa.Column("released_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("deal_escrows", sa.Column("refunded_at", sa.DateTime(timezone=True), nullable=True))

    op.add_column("users", sa.Column("ton_wallet_address", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "ton_wallet_address")

    op.drop_column("deal_escrows", "refunded_at")
    op.drop_column("deal_escrows", "released_at")
    op.drop_column("deal_escrows", "refunded_amount_ton")
    op.drop_column("deal_escrows", "released_amount_ton")
    op.drop_column("deal_escrows", "refund_tx_hash")
    op.drop_column("deal_escrows", "release_tx_hash")

    op.drop_column("deals", "verified_at")
    op.drop_column("deals", "posted_content_hash")
    op.drop_column("deals", "posted_message_id")
    op.drop_column("deals", "posted_at")
    op.drop_column("deals", "verification_window_hours")
    op.drop_column("deals", "scheduled_at")
