"""add campaign application placement terms and relax campaign deal term constraint

Revision ID: a9d4b7c2e1f0
Revises: f1a9c3d4e5b6
Create Date: 2026-02-09 00:00:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "a9d4b7c2e1f0"
down_revision = "f1a9c3d4e5b6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "campaign_applications",
        sa.Column("proposed_placement_type", sa.String(), nullable=True),
    )
    op.add_column(
        "campaign_applications",
        sa.Column("proposed_exclusive_hours", sa.Integer(), nullable=True),
    )
    op.add_column(
        "campaign_applications",
        sa.Column("proposed_retention_hours", sa.Integer(), nullable=True),
    )

    op.execute(
        """
        UPDATE campaign_applications
        SET proposed_placement_type = CASE
            WHEN lower(proposed_format_label) IN ('post', 'story') THEN lower(proposed_format_label)
            ELSE 'post'
        END
        """
    )
    op.execute("UPDATE campaign_applications SET proposed_exclusive_hours = 0")
    op.execute("UPDATE campaign_applications SET proposed_retention_hours = 24")

    op.alter_column("campaign_applications", "proposed_placement_type", nullable=False)
    op.alter_column("campaign_applications", "proposed_exclusive_hours", nullable=False)
    op.alter_column("campaign_applications", "proposed_retention_hours", nullable=False)

    op.create_check_constraint(
        "ck_campaign_applications_proposed_placement_type",
        "campaign_applications",
        "proposed_placement_type IN ('post', 'story')",
    )
    op.create_check_constraint(
        "ck_campaign_applications_proposed_exclusive_hours",
        "campaign_applications",
        "proposed_exclusive_hours >= 0",
    )
    op.create_check_constraint(
        "ck_campaign_applications_proposed_retention_hours",
        "campaign_applications",
        "proposed_retention_hours >= 1",
    )

    op.drop_constraint("ck_deals_listing_terms", "deals", type_="check")
    op.create_check_constraint(
        "ck_deals_listing_terms",
        "deals",
        "(source_type = 'listing' AND placement_type IS NOT NULL "
        "AND exclusive_hours IS NOT NULL AND retention_hours IS NOT NULL) OR "
        "(source_type = 'campaign')",
    )


def downgrade() -> None:
    op.drop_constraint("ck_deals_listing_terms", "deals", type_="check")
    op.create_check_constraint(
        "ck_deals_listing_terms",
        "deals",
        "(source_type = 'listing' AND placement_type IS NOT NULL "
        "AND exclusive_hours IS NOT NULL AND retention_hours IS NOT NULL) OR "
        "(source_type = 'campaign' AND placement_type IS NULL "
        "AND exclusive_hours IS NULL AND retention_hours IS NULL)",
    )

    op.drop_constraint(
        "ck_campaign_applications_proposed_retention_hours",
        "campaign_applications",
        type_="check",
    )
    op.drop_constraint(
        "ck_campaign_applications_proposed_exclusive_hours",
        "campaign_applications",
        type_="check",
    )
    op.drop_constraint(
        "ck_campaign_applications_proposed_placement_type",
        "campaign_applications",
        type_="check",
    )

    op.drop_column("campaign_applications", "proposed_retention_hours")
    op.drop_column("campaign_applications", "proposed_exclusive_hours")
    op.drop_column("campaign_applications", "proposed_placement_type")
