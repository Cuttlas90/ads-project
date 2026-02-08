"""add structured listing formats

Revision ID: c8f1d2a3b4c5
Revises: b1d7e3a4c9f0
Create Date: 2026-02-08 17:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "c8f1d2a3b4c5"
down_revision = "b1d7e3a4c9f0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("listing_formats", sa.Column("placement_type", sa.String(), nullable=True))
    op.add_column("listing_formats", sa.Column("exclusive_hours", sa.Integer(), nullable=True))
    op.add_column("listing_formats", sa.Column("retention_hours", sa.Integer(), nullable=True))

    listing_formats = sa.table(
        "listing_formats",
        sa.column("label", sa.String()),
        sa.column("placement_type", sa.String()),
        sa.column("exclusive_hours", sa.Integer()),
        sa.column("retention_hours", sa.Integer()),
    )
    op.execute(
        listing_formats.update().values(
            placement_type=sa.case(
                (
                    sa.func.lower(sa.func.coalesce(listing_formats.c.label, "")).like("%story%"),
                    "story",
                ),
                else_="post",
            ),
            exclusive_hours=0,
            retention_hours=24,
        )
    )

    with op.batch_alter_table("listing_formats") as batch_op:
        batch_op.alter_column("placement_type", existing_type=sa.String(), nullable=False)
        batch_op.alter_column("exclusive_hours", existing_type=sa.Integer(), nullable=False)
        batch_op.alter_column("retention_hours", existing_type=sa.Integer(), nullable=False)
        batch_op.drop_constraint("ux_listing_formats_listing_label", type_="unique")
        batch_op.create_check_constraint(
            "ck_listing_formats_placement_type",
            "placement_type IN ('post', 'story')",
        )
        batch_op.create_check_constraint(
            "ck_listing_formats_exclusive_hours",
            "exclusive_hours >= 0",
        )
        batch_op.create_check_constraint(
            "ck_listing_formats_retention_hours",
            "retention_hours >= 1",
        )
        batch_op.create_unique_constraint(
            "ux_listing_formats_listing_terms",
            ["listing_id", "placement_type", "exclusive_hours", "retention_hours"],
        )
        batch_op.drop_column("label")

    op.add_column("deals", sa.Column("placement_type", sa.String(), nullable=True))
    op.add_column("deals", sa.Column("exclusive_hours", sa.Integer(), nullable=True))
    op.add_column("deals", sa.Column("retention_hours", sa.Integer(), nullable=True))

    op.execute(
        sa.text(
            """
            UPDATE deals
            SET
              placement_type = (
                SELECT listing_formats.placement_type
                FROM listing_formats
                WHERE listing_formats.id = deals.listing_format_id
              ),
              exclusive_hours = (
                SELECT listing_formats.exclusive_hours
                FROM listing_formats
                WHERE listing_formats.id = deals.listing_format_id
              ),
              retention_hours = (
                SELECT listing_formats.retention_hours
                FROM listing_formats
                WHERE listing_formats.id = deals.listing_format_id
              )
            WHERE source_type = 'listing'
            """
        )
    )
    op.execute(
        sa.text(
            """
            UPDATE deals
            SET verification_window_hours = COALESCE(verification_window_hours, retention_hours, 24)
            WHERE source_type = 'listing'
            """
        )
    )

    with op.batch_alter_table("deals") as batch_op:
        batch_op.create_check_constraint(
            "ck_deals_placement_type",
            "placement_type IS NULL OR placement_type IN ('post', 'story')",
        )
        batch_op.create_check_constraint(
            "ck_deals_exclusive_hours",
            "exclusive_hours IS NULL OR exclusive_hours >= 0",
        )
        batch_op.create_check_constraint(
            "ck_deals_retention_hours",
            "retention_hours IS NULL OR retention_hours >= 1",
        )
        batch_op.create_check_constraint(
            "ck_deals_listing_terms",
            "(source_type = 'listing' AND placement_type IS NOT NULL "
            "AND exclusive_hours IS NOT NULL AND retention_hours IS NOT NULL) OR "
            "(source_type = 'campaign' AND placement_type IS NULL "
            "AND exclusive_hours IS NULL AND retention_hours IS NULL)",
        )
        batch_op.create_index("ix_deals_placement_type", ["placement_type"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("deals") as batch_op:
        batch_op.drop_index("ix_deals_placement_type")
        batch_op.drop_constraint("ck_deals_listing_terms", type_="check")
        batch_op.drop_constraint("ck_deals_retention_hours", type_="check")
        batch_op.drop_constraint("ck_deals_exclusive_hours", type_="check")
        batch_op.drop_constraint("ck_deals_placement_type", type_="check")
        batch_op.drop_column("retention_hours")
        batch_op.drop_column("exclusive_hours")
        batch_op.drop_column("placement_type")

    op.add_column("listing_formats", sa.Column("label", sa.String(), nullable=True))
    listing_formats = sa.table(
        "listing_formats",
        sa.column("placement_type", sa.String()),
        sa.column("exclusive_hours", sa.Integer()),
        sa.column("retention_hours", sa.Integer()),
        sa.column("label", sa.String()),
    )
    label_expr = (
        sa.case((listing_formats.c.placement_type == "story", "Story"), else_="Post")
        + sa.literal(" ")
        + sa.cast(sa.func.coalesce(listing_formats.c.exclusive_hours, 0), sa.String())
        + sa.literal("h/")
        + sa.cast(sa.func.coalesce(listing_formats.c.retention_hours, 24), sa.String())
        + sa.literal("h")
    )
    op.execute(listing_formats.update().values(label=label_expr))

    with op.batch_alter_table("listing_formats") as batch_op:
        batch_op.drop_constraint("ux_listing_formats_listing_terms", type_="unique")
        batch_op.drop_constraint("ck_listing_formats_retention_hours", type_="check")
        batch_op.drop_constraint("ck_listing_formats_exclusive_hours", type_="check")
        batch_op.drop_constraint("ck_listing_formats_placement_type", type_="check")
        batch_op.alter_column("label", existing_type=sa.String(), nullable=False)
        batch_op.create_unique_constraint("ux_listing_formats_listing_label", ["listing_id", "label"])
        batch_op.drop_column("retention_hours")
        batch_op.drop_column("exclusive_hours")
        batch_op.drop_column("placement_type")
