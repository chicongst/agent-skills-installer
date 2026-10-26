"""create todos

Revision ID: f230c2458f16
Revises:
Create Date: 2026-10-26 13:45:35.511179
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "f230c2458f16"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    op.create_table(
        "todos",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("owner_id", sa.String(length=128), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.String(length=5000), nullable=True),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column(
            "priority",
            sa.Enum("low", "medium", "high", name="priority", native_enum=False, create_constraint=True, length=10),
            nullable=True,
        ),
        sa.Column(
            "status",
            sa.Enum("open", "done", name="status", native_enum=False, create_constraint=True, length=10),
            nullable=False,
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("version >= 1", name=op.f("ck_todos_version_positive")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_todos")),
    )
    op.create_index("ix_todos_owner_due_date", "todos", ["owner_id", "due_date", "id"], unique=False)
    op.create_index("ix_todos_owner_status_created", "todos", ["owner_id", "status", "created_at", "id"], unique=False)
    op.create_index(
        "ix_todos_title_trgm",
        "todos",
        ["title"],
        unique=False,
        postgresql_using="gin",
        postgresql_ops={"title": "gin_trgm_ops"},
    )


def downgrade() -> None:
    op.drop_index(
        "ix_todos_title_trgm", table_name="todos", postgresql_using="gin", postgresql_ops={"title": "gin_trgm_ops"}
    )
    op.drop_index("ix_todos_owner_status_created", table_name="todos")
    op.drop_index("ix_todos_owner_due_date", table_name="todos")
    op.drop_table("todos")
