"""ticket closing document attachment type

Revision ID: d8a4f2c9b3e1
Revises: c7f2a9e4b1d6
Create Date: 2026-07-28

"""
from collections.abc import Sequence

from alembic import op

revision: str = "d8a4f2c9b3e1"
down_revision: str | None = "c7f2a9e4b1d6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("ALTER TYPE attachment_type ADD VALUE IF NOT EXISTS 'document'")


def downgrade() -> None:
    # PostgreSQL does not support removing a value from an enum type; the
    # 'document' value is left in place on downgrade (harmless if unused).
    pass
