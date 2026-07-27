"""admin role, permissions and avatar

Revision ID: c7f2a9e4b1d6
Revises: b4e8f1c9d3a7
Create Date: 2026-07-27

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "c7f2a9e4b1d6"
down_revision: str | None = "b4e8f1c9d3a7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("ALTER TYPE user_role ADD VALUE IF NOT EXISTS 'admin'")
    op.add_column("users", sa.Column("permissions", sa.JSON(), nullable=True))
    op.add_column("users", sa.Column("avatar_path", sa.String(255), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "avatar_path")
    op.drop_column("users", "permissions")
    # PostgreSQL does not support removing a value from an enum type; the
    # 'admin' value is left in place on downgrade (harmless if unused).
