"""merge inventory faculty/sub_unit into one location, add mac_address

Revision ID: f3a6c8e1d4b9
Revises: e1c6a3f8d5b2
Create Date: 2026-08-18

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "f3a6c8e1d4b9"
down_revision: str | None = "e1c6a3f8d5b2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("inventory_items", sa.Column("mac_address", sa.String(length=32), nullable=True))
    op.drop_column("inventory_items", "sub_unit")


def downgrade() -> None:
    op.add_column("inventory_items", sa.Column("sub_unit", sa.String(length=255), nullable=True))
    op.drop_column("inventory_items", "mac_address")
