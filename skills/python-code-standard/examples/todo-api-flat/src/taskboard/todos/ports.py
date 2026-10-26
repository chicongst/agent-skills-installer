from dataclasses import dataclass, field
from enum import StrEnum
from typing import Protocol
from uuid import UUID

from taskboard.shared.pagination import Page, PageRequest
from taskboard.todos.domain import TodoItem, TodoStatus


class TodoSortField(StrEnum):
    CREATED_AT = "created_at"
    DUE_DATE = "due_date"


@dataclass(frozen=True, slots=True)
class TodoSort:
    field: TodoSortField = TodoSortField.CREATED_AT
    descending: bool = True


@dataclass(frozen=True, slots=True, kw_only=True)
class TodoListQuery:
    owner_id: str
    status: TodoStatus | None = None
    search: str | None = None
    sort: TodoSort = field(default_factory=TodoSort)
    page: PageRequest = field(default_factory=PageRequest)


@dataclass(frozen=True, slots=True)
class Written:
    pass


@dataclass(frozen=True, slots=True)
class Missing:
    pass


@dataclass(frozen=True, slots=True)
class Stale:
    current_version: int


type WriteResult = Written | Missing | Stale


class TodoRepository(Protocol):
    """Storage port. Every method is scoped to one owner; another owner's todo behaves as missing.
    A database adapter must keep these semantics: case-insensitive substring search on the title with wildcards
    taken literally, nulls last in both sort directions, ties broken by id, and version-guarded writes.
    """

    async def add(self, todo: TodoItem) -> None: ...

    async def get(self, owner_id: str, todo_id: UUID) -> TodoItem | None: ...

    async def list(self, query: TodoListQuery) -> Page[TodoItem]: ...

    async def update(self, todo: TodoItem, expected_version: int) -> WriteResult:
        """Save `todo` only if the stored version still equals `expected_version`; report the current one if not."""
        ...

    async def delete(self, owner_id: str, todo_id: UUID, expected_version: int) -> WriteResult: ...
