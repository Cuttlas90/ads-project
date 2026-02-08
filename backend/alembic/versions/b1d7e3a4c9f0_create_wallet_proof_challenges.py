"""create wallet proof challenges

Revision ID: b1d7e3a4c9f0
Revises: a6c3e5f7b8d9
Create Date: 2026-02-08 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "b1d7e3a4c9f0"
down_revision = "a6c3e5f7b8d9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "wallet_proof_challenges",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("challenge", sa.String(length=128), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_wallet_proof_challenges_user_id"), "wallet_proof_challenges", ["user_id"], unique=False)
    op.create_index(op.f("ix_wallet_proof_challenges_challenge"), "wallet_proof_challenges", ["challenge"], unique=True)
    op.create_index(op.f("ix_wallet_proof_challenges_expires_at"), "wallet_proof_challenges", ["expires_at"], unique=False)
    op.create_index(op.f("ix_wallet_proof_challenges_consumed_at"), "wallet_proof_challenges", ["consumed_at"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_wallet_proof_challenges_consumed_at"), table_name="wallet_proof_challenges")
    op.drop_index(op.f("ix_wallet_proof_challenges_expires_at"), table_name="wallet_proof_challenges")
    op.drop_index(op.f("ix_wallet_proof_challenges_challenge"), table_name="wallet_proof_challenges")
    op.drop_index(op.f("ix_wallet_proof_challenges_user_id"), table_name="wallet_proof_challenges")
    op.drop_table("wallet_proof_challenges")
