"""add campaign lifecycle and multi-acceptance support

Revision ID: f1a9c3d4e5b6
Revises: c8f1d2a3b4c5
Create Date: 2026-02-08 00:00:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "f1a9c3d4e5b6"
down_revision = "c8f1d2a3b4c5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "campaign_requests",
        sa.Column("lifecycle_state", sa.String(), server_default=sa.text("'active'"), nullable=False),
    )
    op.add_column(
        "campaign_requests",
        sa.Column("max_acceptances", sa.Integer(), server_default=sa.text("10"), nullable=False),
    )
    op.add_column(
        "campaign_requests",
        sa.Column("hidden_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_check_constraint(
        "ck_campaign_requests_lifecycle_state",
        "campaign_requests",
        "lifecycle_state IN ('active', 'hidden', 'closed_by_limit')",
    )
    op.create_check_constraint(
        "ck_campaign_requests_max_acceptances",
        "campaign_requests",
        "max_acceptances >= 1",
    )
    op.create_index(
        op.f("ix_campaign_requests_lifecycle_state"),
        "campaign_requests",
        ["lifecycle_state"],
        unique=False,
    )
    op.execute("UPDATE campaign_requests SET lifecycle_state = 'hidden' WHERE is_active = false")

    op.add_column(
        "campaign_applications",
        sa.Column("hidden_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        op.f("ix_campaign_applications_hidden_at"),
        "campaign_applications",
        ["hidden_at"],
        unique=False,
    )

    op.drop_constraint("ux_deals_campaign_id", "deals", type_="unique")


def downgrade() -> None:
    op.create_unique_constraint("ux_deals_campaign_id", "deals", ["campaign_id"])

    op.drop_index(op.f("ix_campaign_applications_hidden_at"), table_name="campaign_applications")
    op.drop_column("campaign_applications", "hidden_at")

    op.drop_index(op.f("ix_campaign_requests_lifecycle_state"), table_name="campaign_requests")
    op.drop_constraint("ck_campaign_requests_max_acceptances", "campaign_requests", type_="check")
    op.drop_constraint("ck_campaign_requests_lifecycle_state", "campaign_requests", type_="check")
    op.drop_column("campaign_requests", "hidden_at")
    op.drop_column("campaign_requests", "max_acceptances")
    op.drop_column("campaign_requests", "lifecycle_state")
