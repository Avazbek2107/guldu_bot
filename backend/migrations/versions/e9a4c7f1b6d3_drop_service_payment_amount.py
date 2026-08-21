"""drop service_payments.amount

Revision ID: e9a4c7f1b6d3
Revises: d6b3f9e2a5c8
Create Date: 2026-08-21

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "e9a4c7f1b6d3"
down_revision: str | None = "d6b3f9e2a5c8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_column("service_payments", "amount")


def downgrade() -> None:
    op.add_column("service_payments", sa.Column("amount", sa.Numeric(precision=12, scale=2), nullable=True))
