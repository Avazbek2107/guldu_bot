"""initial schema

Revision ID: 8f3a1c2e4b6d
Revises:
Create Date: 2026-07-21

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "8f3a1c2e4b6d"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

user_role = sa.Enum(
    "super_admin", "technician_main", "technician_backup", "faculty_staff", name="user_role"
)
ticket_category = sa.Enum(
    "computer", "network", "projector", "power", "printer", "software", "other", name="ticket_category"
)
ticket_priority = sa.Enum("urgent", "normal", name="ticket_priority")
ticket_status = sa.Enum("open", "in_progress", "closed", name="ticket_status")
attachment_type = sa.Enum("photo", "video", name="attachment_type")


def upgrade() -> None:
    op.create_table(
        "faculties",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False, unique=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("telegram_id", sa.BigInteger(), nullable=True, unique=True),
        sa.Column("username", sa.String(100), nullable=True, unique=True),
        sa.Column("password_hash", sa.String(255), nullable=True),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("phone", sa.String(32), nullable=False),
        sa.Column("faculty_id", sa.Integer(), sa.ForeignKey("faculties.id"), nullable=True),
        sa.Column("role", user_role, nullable=False),
        sa.Column("is_blocked", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_suspicious", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_one_main_technician_per_faculty",
        "users",
        ["faculty_id"],
        unique=True,
        postgresql_where=sa.text("role = 'technician_main'"),
    )

    op.create_table(
        "tickets",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("ticket_number", sa.String(32), nullable=False, unique=True),
        sa.Column("created_by_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("faculty_id", sa.Integer(), sa.ForeignKey("faculties.id"), nullable=False),
        sa.Column("category", ticket_category, nullable=False),
        sa.Column("priority", ticket_priority, nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("status", ticket_status, nullable=False, server_default="open"),
        sa.Column("assigned_technician_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("resolution_comment", sa.Text(), nullable=True),
        sa.Column("is_suspicious", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("suspicious_comment", sa.Text(), nullable=True),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("sla_deadline", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
            nullable=False,
        ),
    )

    op.create_table(
        "ticket_attachments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("ticket_id", sa.Integer(), sa.ForeignKey("tickets.id"), nullable=False),
        sa.Column("file_path", sa.String(500), nullable=False),
        sa.Column("file_type", attachment_type, nullable=False),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "ticket_reassignments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("ticket_id", sa.Integer(), sa.ForeignKey("tickets.id"), nullable=False),
        sa.Column("from_technician_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("to_technician_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "ratings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("ticket_id", sa.Integer(), sa.ForeignKey("tickets.id"), nullable=False, unique=True),
        sa.Column("stars", sa.Integer(), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("stars >= 1 AND stars <= 5", name="ck_rating_stars_range"),
    )

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("actor_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("entity_type", sa.String(50), nullable=False),
        sa.Column("entity_id", sa.Integer(), nullable=False),
        sa.Column("details", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_table("ratings")
    op.drop_table("ticket_reassignments")
    op.drop_table("ticket_attachments")
    op.drop_table("tickets")
    op.drop_index("ix_one_main_technician_per_faculty", table_name="users")
    op.drop_table("users")
    op.drop_table("faculties")

    user_role.drop(op.get_bind(), checkfirst=True)
    ticket_category.drop(op.get_bind(), checkfirst=True)
    ticket_priority.drop(op.get_bind(), checkfirst=True)
    ticket_status.drop(op.get_bind(), checkfirst=True)
    attachment_type.drop(op.get_bind(), checkfirst=True)
