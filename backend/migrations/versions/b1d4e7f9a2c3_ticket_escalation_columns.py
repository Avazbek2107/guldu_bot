"""ticket escalation columns

Revision ID: b1d4e7f9a2c3
Revises: 8f3a1c2e4b6d
Create Date: 2026-07-21

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "b1d4e7f9a2c3"
down_revision: str | None = "8f3a1c2e4b6d"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("tickets", sa.Column("escalated_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("tickets", sa.Column("sla_breach_notified_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("tickets", "sla_breach_notified_at")
    op.drop_column("tickets", "escalated_at")
