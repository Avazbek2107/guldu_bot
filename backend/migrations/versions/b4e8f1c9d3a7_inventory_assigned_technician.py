"""inventory item assigned technician

Revision ID: b4e8f1c9d3a7
Revises: 9a1c4e7b2f0d
Create Date: 2026-07-27

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "b4e8f1c9d3a7"
down_revision: str | None = "9a1c4e7b2f0d"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "inventory_items",
        sa.Column("assigned_technician_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
    )
    op.create_index(
        "ix_inventory_items_assigned_technician_id", "inventory_items", ["assigned_technician_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_inventory_items_assigned_technician_id", table_name="inventory_items")
    op.drop_column("inventory_items", "assigned_technician_id")
