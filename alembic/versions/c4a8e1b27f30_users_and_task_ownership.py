"""users and task ownership

Revision ID: c4a8e1b27f30
Revises: 9731208f4770
Create Date: 2026-10-23 16:55:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c4a8e1b27f30"
down_revision: Union[str, None] = "9731208f4770"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.execute("DELETE FROM tasks")
    with op.batch_alter_table("tasks") as batch:
        batch.add_column(sa.Column("user_id", sa.Integer(), nullable=False))
        batch.create_index("ix_tasks_user_id", ["user_id"])
        batch.create_foreign_key("fk_tasks_user_id", "users", ["user_id"], ["id"])


def downgrade() -> None:
    with op.batch_alter_table("tasks") as batch:
        batch.drop_constraint("fk_tasks_user_id", type_="foreignkey")
        batch.drop_index("ix_tasks_user_id")
        batch.drop_column("user_id")
    op.drop_table("users")
