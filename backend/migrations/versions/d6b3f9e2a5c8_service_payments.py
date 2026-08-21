"""service payments monitoring

Revision ID: d6b3f9e2a5c8
Revises: c4f8a1e6b2d9
Create Date: 2026-08-21

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "d6b3f9e2a5c8"
down_revision: str | None = "c4f8a1e6b2d9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "service_payments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("category", sa.String(length=64), nullable=False),
        sa.Column("amount", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("due_date", sa.Date(), nullable=False),
        sa.Column("responsible_person", sa.String(length=255), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index("ix_service_payments_due_date", "service_payments", ["due_date"])


def downgrade() -> None:
    op.drop_index("ix_service_payments_due_date", table_name="service_payments")
    op.drop_table("service_payments")
