"""normalize channel chat ids for bot api and merge heads

Revision ID: c6e4f9a1b2d3
Revises: a9d4b7c2e1f0, e3b7f5a2c1d9
Create Date: 2026-02-10 00:00:00.000000
"""

from __future__ import annotations

from alembic import op


# revision identifiers, used by Alembic.
revision = "c6e4f9a1b2d3"
down_revision = ("a9d4b7c2e1f0", "e3b7f5a2c1d9")
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        UPDATE channels
        SET telegram_channel_id = -1000000000000 - telegram_channel_id
        WHERE telegram_channel_id IS NOT NULL
          AND telegram_channel_id > 0
          AND telegram_channel_id < 1000000000000
        """
    )


def downgrade() -> None:
    op.execute(
        """
        UPDATE channels
        SET telegram_channel_id = -1000000000000 - telegram_channel_id
        WHERE telegram_channel_id IS NOT NULL
          AND telegram_channel_id <= -1000000000000
          AND telegram_channel_id > -2000000000000
        """
    )
