"""user last_login_at and last_bot_activity_at

Revision ID: b7e2f5a9c3d1
Revises: a2c5d8e1f4b7
Create Date: 2026-08-20

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "b7e2f5a9c3d1"
down_revision: str | None = "a2c5d8e1f4b7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("users", sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("users", sa.Column("last_bot_activity_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "last_bot_activity_at")
    op.drop_column("users", "last_login_at")
