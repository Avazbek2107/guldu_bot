"""technician faculty assignments (multi-faculty technicians)

Revision ID: df116055dcf2
Revises: c2e5f8a1b3d7
Create Date: 2026-07-23

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "df116055dcf2"
down_revision: str | None = "c2e5f8a1b3d7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

technician_faculty_role = sa.Enum(
    "technician_main", "technician_backup", name="technician_faculty_role"
)


def upgrade() -> None:
    op.create_table(
        "technician_faculty_assignments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "faculty_id",
            sa.Integer(),
            sa.ForeignKey("faculties.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("role", technician_faculty_role, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("user_id", "faculty_id", name="uq_tech_faculty_assignment"),
    )
    op.create_index(
        "ix_technician_faculty_assignments_user_id",
        "technician_faculty_assignments",
        ["user_id"],
    )
    op.create_index(
        "ix_technician_faculty_assignments_faculty_id",
        "technician_faculty_assignments",
        ["faculty_id"],
    )
    op.create_index(
        "ix_one_main_tech_per_faculty_assignment",
        "technician_faculty_assignments",
        ["faculty_id"],
        unique=True,
        postgresql_where=sa.text("role = 'technician_main'"),
    )

    # Backfill: convert each existing technician's single (faculty_id, role) into
    # one assignment row before the old per-user constraint is dropped.
    op.execute(
        sa.text(
            "INSERT INTO technician_faculty_assignments (user_id, faculty_id, role, created_at) "
            "SELECT id, faculty_id, role::text::technician_faculty_role, now() FROM users "
            "WHERE role IN ('technician_main', 'technician_backup') AND faculty_id IS NOT NULL"
        )
    )

    op.drop_index("ix_one_main_technician_per_faculty", table_name="users")


def downgrade() -> None:
    op.create_index(
        "ix_one_main_technician_per_faculty",
        "users",
        ["faculty_id"],
        unique=True,
        postgresql_where=sa.text("role = 'technician_main'"),
    )
    op.drop_table("technician_faculty_assignments")
    technician_faculty_role.drop(op.get_bind(), checkfirst=True)
