"""projects

Revision ID: c4f8a1e6b2d9
Revises: b7e2f5a9c3d1
Create Date: 2026-08-21

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "c4f8a1e6b2d9"
down_revision: str | None = "b7e2f5a9c3d1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "projects",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=64), nullable=False, server_default="Rejalashtirilgan"),
        sa.Column("responsible_person", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("projects")
