"""add users preferred role

Revision ID: a6c3e5f7b8d9
Revises: d2f1a3c4b5e6
Create Date: 2026-02-01 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "a6c3e5f7b8d9"
down_revision = "d2f1a3c4b5e6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("preferred_role", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "preferred_role")
