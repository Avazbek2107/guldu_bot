"""inventory items and ticket repair link

Revision ID: 6b78048d5567
Revises: d2b7d70f17fc
Create Date: 2026-07-24

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "6b78048d5567"
down_revision: str | None = "d2b7d70f17fc"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "inventory_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("faculty_id", sa.Integer(), sa.ForeignKey("faculties.id"), nullable=False),
        sa.Column("sub_unit", sa.String(255), nullable=True),
        sa.Column("room", sa.String(64), nullable=True),
        sa.Column("inventory_number", sa.String(64), nullable=True),
        sa.Column("uzasbo", sa.String(255), nullable=True),
        sa.Column("inventory_type", sa.String(128), nullable=True),
        sa.Column("model", sa.String(128), nullable=True),
        sa.Column("status", sa.String(64), nullable=False, server_default="ishchi"),
        sa.Column("internet_connection", sa.String(128), nullable=True),
        sa.Column("responsible_person", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_inventory_items_faculty_id", "inventory_items", ["faculty_id"])
    op.create_index("ix_inventory_items_inventory_number", "inventory_items", ["inventory_number"])

    op.add_column(
        "tickets",
        sa.Column(
            "inventory_item_id",
            sa.Integer(),
            sa.ForeignKey("inventory_items.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.create_index("ix_tickets_inventory_item_id", "tickets", ["inventory_item_id"])


def downgrade() -> None:
    op.drop_index("ix_tickets_inventory_item_id", table_name="tickets")
    op.drop_column("tickets", "inventory_item_id")
    op.drop_index("ix_inventory_items_inventory_number", table_name="inventory_items")
    op.drop_index("ix_inventory_items_faculty_id", table_name="inventory_items")
    op.drop_table("inventory_items")
