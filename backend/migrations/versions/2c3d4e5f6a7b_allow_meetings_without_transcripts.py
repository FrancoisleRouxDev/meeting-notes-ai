"""Allow meetings to be created before their transcript is available.

Revision ID: 2c3d4e5f6a7b
Revises: 1a2b3c4d5e6f
Create Date: 2026-11-25
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect, text

revision: str = "2c3d4e5f6a7b"
down_revision: Union[str, None] = "1a2b3c4d5e6f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    columns = {column["name"]: column for column in inspect(op.get_bind()).get_columns("meetings")}
    if "transcript" in columns and not columns["transcript"]["nullable"]:
        with op.batch_alter_table("meetings") as batch_op:
            batch_op.alter_column(
                "transcript",
                existing_type=sa.Text(),
                existing_nullable=False,
                nullable=True,
            )


def downgrade() -> None:
    columns = {column["name"]: column for column in inspect(op.get_bind()).get_columns("meetings")}
    if "transcript" in columns and columns["transcript"]["nullable"]:
        op.get_bind().execute(text("UPDATE meetings SET transcript = '' WHERE transcript IS NULL"))
        with op.batch_alter_table("meetings") as batch_op:
            batch_op.alter_column(
                "transcript",
                existing_type=sa.Text(),
                existing_nullable=True,
                nullable=False,
            )
