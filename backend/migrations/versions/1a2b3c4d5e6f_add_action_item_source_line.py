"""Add source line to action items.

Revision ID: 1a2b3c4d5e6f
Revises: 0fdecbdf1da7
Create Date: 2026-11-25
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision: str = "1a2b3c4d5e6f"
down_revision: Union[str, None] = "0fdecbdf1da7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    columns = {column["name"] for column in inspect(op.get_bind()).get_columns("action_items")}
    if "source_line" not in columns:
        op.add_column("action_items", sa.Column("source_line", sa.Integer(), nullable=True))


def downgrade() -> None:
    columns = {column["name"] for column in inspect(op.get_bind()).get_columns("action_items")}
    if "source_line" in columns:
        op.drop_column("action_items", "source_line")
