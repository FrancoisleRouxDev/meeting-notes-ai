"""baseline schema

Revision ID: 0fdecbdf1da7
Revises: 
Create Date: 2026-11-25 16:47:33.770787
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision: str = '0fdecbdf1da7'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    existing_tables = set(inspect(op.get_bind()).get_table_names())

    if "users" not in existing_tables:
        op.create_table(
            "users",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("email", sa.String(length=255), nullable=False),
            sa.Column("password_hash", sa.String(length=255), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_users_email", "users", ["email"], unique=True)

    if "meetings" not in existing_tables:
        op.create_table(
            "meetings",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("title", sa.String(length=200), nullable=False),
            sa.Column("meeting_date", sa.Date(), nullable=False),
            sa.Column("transcript", sa.Text(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("summary", sa.Text(), nullable=True),
            sa.Column("decisions", sa.JSON(), nullable=True),
            sa.Column("analysis_status", sa.String(length=20), nullable=False),
            sa.Column("analysis_error", sa.String(length=200), nullable=True),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_meetings_user_id", "meetings", ["user_id"], unique=False)

    if "password_reset_tokens" not in existing_tables:
        op.create_table(
            "password_reset_tokens",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("token_hash", sa.String(length=64), nullable=False),
            sa.Column("expires_at", sa.DateTime(), nullable=False),
            sa.Column("used_at", sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("token_hash"),
        )
        op.create_index(
            "ix_password_reset_tokens_user_id",
            "password_reset_tokens",
            ["user_id"],
            unique=False,
        )

    if "sessions" not in existing_tables:
        op.create_table(
            "sessions",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("token_hash", sa.String(length=64), nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_sessions_token_hash", "sessions", ["token_hash"], unique=True)

    if "slack_connections" not in existing_tables:
        op.create_table(
            "slack_connections",
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("webhook_encrypted", sa.String(length=1000), nullable=False),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
            sa.PrimaryKeyConstraint("user_id"),
        )

    if "action_items" not in existing_tables:
        op.create_table(
            "action_items",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("meeting_id", sa.Integer(), nullable=False),
            sa.Column("text", sa.String(length=500), nullable=False),
            sa.Column("owner", sa.String(length=100), nullable=True),
            sa.Column("due_date", sa.Date(), nullable=True),
            sa.Column("status", sa.String(length=20), nullable=False),
            sa.ForeignKeyConstraint(["meeting_id"], ["meetings.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_action_items_meeting_id", "action_items", ["meeting_id"], unique=False)


def downgrade() -> None:
    # Existing databases may be adopted at this revision, so never drop their tables here.
    pass
