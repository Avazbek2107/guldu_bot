"""faculty unit_type (faculty vs department)

Revision ID: d2b7d70f17fc
Revises: 630e20ada337
Create Date: 2026-07-24

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "d2b7d70f17fc"
down_revision: str | None = "630e20ada337"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

org_unit_type = sa.Enum("faculty", "department", name="org_unit_type")


def upgrade() -> None:
    org_unit_type.create(op.get_bind(), checkfirst=True)
    op.add_column(
        "faculties",
        sa.Column("unit_type", org_unit_type, nullable=False, server_default="faculty"),
    )


def downgrade() -> None:
    op.drop_column("faculties", "unit_type")
    org_unit_type.drop(op.get_bind(), checkfirst=True)
