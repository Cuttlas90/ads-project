"""create deal escrows

Revision ID: f6a2d8c1b3e4
Revises: c4a8f1d9e7b2
Create Date: 2026-01-31 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "f6a2d8c1b3e4"
down_revision = "c4a8f1d9e7b2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "deal_escrows",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("deal_id", sa.Integer(), nullable=False),
        sa.Column("state", sa.String(), nullable=False),
        sa.Column("deposit_address", sa.String(), nullable=True),
        sa.Column("expected_amount_ton", sa.Numeric(18, 9), nullable=True),
        sa.Column("received_amount_ton", sa.Numeric(18, 9), nullable=True),
        sa.Column("deposit_tx_hash", sa.String(), nullable=True),
        sa.Column("deposit_confirmations", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("fee_percent", sa.Numeric(5, 2), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["deal_id"], ["deals.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("deal_id", name="ux_deal_escrows_deal_id"),
        sa.UniqueConstraint("deposit_address"),
    )
    op.create_index(op.f("ix_deal_escrows_deal_id"), "deal_escrows", ["deal_id"], unique=False)
    op.create_index(op.f("ix_deal_escrows_deposit_tx_hash"), "deal_escrows", ["deposit_tx_hash"], unique=False)
    op.create_index(op.f("ix_deal_escrows_state"), "deal_escrows", ["state"], unique=False)

    op.create_table(
        "escrow_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("escrow_id", sa.Integer(), nullable=False),
        sa.Column("actor_user_id", sa.Integer(), nullable=True),
        sa.Column("from_state", sa.String(), nullable=True),
        sa.Column("to_state", sa.String(), nullable=False),
        sa.Column("event_type", sa.String(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["escrow_id"], ["deal_escrows.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_escrow_events_escrow_id"), "escrow_events", ["escrow_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_escrow_events_escrow_id"), table_name="escrow_events")
    op.drop_table("escrow_events")

    op.drop_index(op.f("ix_deal_escrows_state"), table_name="deal_escrows")
    op.drop_index(op.f("ix_deal_escrows_deposit_tx_hash"), table_name="deal_escrows")
    op.drop_index(op.f("ix_deal_escrows_deal_id"), table_name="deal_escrows")
    op.drop_table("deal_escrows")
