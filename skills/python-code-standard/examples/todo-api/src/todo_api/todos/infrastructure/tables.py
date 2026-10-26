from datetime import date, datetime
from uuid import UUID

from sqlalchemy import CheckConstraint, DateTime, Enum, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from todo_api.infrastructure.database import Base
from todo_api.shared.identity import OWNER_ID_MAX_LENGTH
from todo_api.todos.domain.todo import DESCRIPTION_MAX_LENGTH, TITLE_MAX_LENGTH, TodoItem, TodoPriority, TodoStatus


def _values(enum: type[TodoStatus | TodoPriority]) -> list[str]:
    return [member.value for member in enum]


class TodoRow(Base):
    __tablename__ = "todos"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    owner_id: Mapped[str] = mapped_column(String(OWNER_ID_MAX_LENGTH))
    title: Mapped[str] = mapped_column(String(TITLE_MAX_LENGTH))
    description: Mapped[str | None] = mapped_column(String(DESCRIPTION_MAX_LENGTH))
    due_date: Mapped[date | None]
    priority: Mapped[TodoPriority | None] = mapped_column(
        Enum(
            TodoPriority, native_enum=False, length=10, values_callable=_values, create_constraint=True, name="priority"
        )
    )
    status: Mapped[TodoStatus] = mapped_column(
        Enum(TodoStatus, native_enum=False, length=10, values_callable=_values, create_constraint=True, name="status")
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    version: Mapped[int]
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    __table_args__ = (
        CheckConstraint("version >= 1", name="version_positive"),
        Index("ix_todos_owner_status_created", "owner_id", "status", "created_at", "id"),
        Index("ix_todos_owner_due_date", "owner_id", "due_date", "id"),
        Index(
            "ix_todos_title_trgm",
            "title",
            postgresql_using="gin",
            postgresql_ops={"title": "gin_trgm_ops"},
        ),
    )


COLUMNS = tuple(column.key for column in TodoRow.__table__.columns)


def to_values(todo: TodoItem) -> dict[str, object]:
    """Every column comes from the aggregate, so a new column cannot be silently left out of an update."""
    return {column: getattr(todo, column) for column in COLUMNS}


def to_domain(row: TodoRow) -> TodoItem:
    return TodoItem(**{column: getattr(row, column) for column in COLUMNS})
