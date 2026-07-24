"""drop unused ratings table and sla columns

Revision ID: 9a1c4e7b2f0d
Revises: 6b78048d5567
Create Date: 2026-07-24

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "9a1c4e7b2f0d"
down_revision: str | None = "6b78048d5567"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_column("tickets", "sla_deadline")
    op.drop_column("tickets", "sla_breach_notified_at")
    op.drop_table("ratings")


def downgrade() -> None:
    op.create_table(
        "ratings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("ticket_id", sa.Integer(), sa.ForeignKey("tickets.id"), unique=True, nullable=False),
        sa.Column("stars", sa.Integer(), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.CheckConstraint("stars >= 1 AND stars <= 5", name="ck_rating_stars_range"),
    )
    op.add_column("tickets", sa.Column("sla_breach_notified_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("tickets", sa.Column("sla_deadline", sa.DateTime(timezone=True), nullable=True))
