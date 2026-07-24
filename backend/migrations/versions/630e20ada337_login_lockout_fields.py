"""login brute-force lockout fields on users

Revision ID: 630e20ada337
Revises: df116055dcf2
Create Date: 2026-07-23

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "630e20ada337"
down_revision: str | None = "df116055dcf2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("failed_login_attempts", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "users",
        sa.Column("locked_until", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("users", "locked_until")
    op.drop_column("users", "failed_login_attempts")
