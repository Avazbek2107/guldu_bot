"""faculty parent_id for nested kafedra structure

Revision ID: e1c6a3f8d5b2
Revises: d8a4f2c9b3e1
Create Date: 2026-07-29

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "e1c6a3f8d5b2"
down_revision: str | None = "d8a4f2c9b3e1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "faculties",
        sa.Column("parent_id", sa.Integer(), sa.ForeignKey("faculties.id", ondelete="CASCADE"), nullable=True),
    )
    op.create_index("ix_faculties_parent_id", "faculties", ["parent_id"])


def downgrade() -> None:
    op.drop_index("ix_faculties_parent_id", table_name="faculties")
    op.drop_column("faculties", "parent_id")
