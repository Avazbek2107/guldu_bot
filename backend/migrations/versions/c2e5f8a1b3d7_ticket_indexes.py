"""ticket performance indexes

Revision ID: c2e5f8a1b3d7
Revises: b1d4e7f9a2c3
Create Date: 2026-07-23

"""
from collections.abc import Sequence

from alembic import op

revision: str = "c2e5f8a1b3d7"
down_revision: str | None = "b1d4e7f9a2c3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index("ix_tickets_faculty_id", "tickets", ["faculty_id"])
    op.create_index("ix_tickets_status", "tickets", ["status"])
    op.create_index("ix_tickets_assigned_technician_id", "tickets", ["assigned_technician_id"])
    op.create_index("ix_tickets_created_at", "tickets", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_tickets_created_at", table_name="tickets")
    op.drop_index("ix_tickets_assigned_technician_id", table_name="tickets")
    op.drop_index("ix_tickets_status", table_name="tickets")
    op.drop_index("ix_tickets_faculty_id", table_name="tickets")
