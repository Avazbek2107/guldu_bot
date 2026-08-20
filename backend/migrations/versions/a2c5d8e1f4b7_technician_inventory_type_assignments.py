"""technician inventory type assignments

Revision ID: a2c5d8e1f4b7
Revises: f3a6c8e1d4b9
Create Date: 2026-08-20

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "a2c5d8e1f4b7"
down_revision: str | None = "f3a6c8e1d4b9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "technician_inventory_type_assignments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("inventory_type", sa.String(length=128), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("inventory_type", name="uq_one_technician_per_inventory_type"),
    )
    op.create_index(
        "ix_technician_inventory_type_assignments_user_id",
        "technician_inventory_type_assignments",
        ["user_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_technician_inventory_type_assignments_user_id",
        table_name="technician_inventory_type_assignments",
    )
    op.drop_table("technician_inventory_type_assignments")
