import asyncio
from datetime import date
from uuid import UUID

from taskboard.shared.pagination import Page
from taskboard.todos.domain import TodoItem
from taskboard.todos.ports import Missing, Stale, TodoListQuery, TodoSortField, WriteResult, Written


class InMemoryTodoRepository:
    """Development and test backend with the semantics a SQL adapter must match (`lower()` like ILIKE, nulls last,
    id tie-break). Holds state, so it is a process singleton; the lock makes check-and-write atomic.
    """

    def __init__(self) -> None:
        self._items: dict[UUID, TodoItem] = {}
        self._lock = asyncio.Lock()

    async def add(self, todo: TodoItem) -> None:
        async with self._lock:
            self._items[todo.id] = todo

    async def get(self, owner_id: str, todo_id: UUID) -> TodoItem | None:
        todo = self._items.get(todo_id)
        return todo if todo is not None and todo.owner_id == owner_id else None

    async def list(self, query: TodoListQuery) -> Page[TodoItem]:
        needle = (query.search or "").lower()
        matches = [
            todo
            for todo in self._items.values()
            if todo.owner_id == query.owner_id
            and (query.status is None or todo.status is query.status)
            and needle in todo.title.lower()
        ]
        ordered = _ordered(matches, query)
        start = query.page.offset
        return Page(
            items=ordered[start : start + query.page.limit],
            total=len(ordered),
            limit=query.page.limit,
            offset=query.page.offset,
        )

    async def update(self, todo: TodoItem, expected_version: int) -> WriteResult:
        async with self._lock:
            result = self._check(todo.owner_id, todo.id, expected_version)
            if isinstance(result, Written):
                self._items[todo.id] = todo
            return result

    async def delete(self, owner_id: str, todo_id: UUID, expected_version: int) -> WriteResult:
        async with self._lock:
            result = self._check(owner_id, todo_id, expected_version)
            if isinstance(result, Written):
                del self._items[todo_id]
            return result

    def _check(self, owner_id: str, todo_id: UUID, expected_version: int) -> WriteResult:
        current = self._items.get(todo_id)
        if current is None or current.owner_id != owner_id:
            return Missing()
        return Written() if current.version == expected_version else Stale(current.version)


def _ordered(todos: list[TodoItem], query: TodoListQuery) -> list[TodoItem]:
    """Python's sort is stable: sorting by id first makes ties deterministic in the requested direction."""
    descending = query.sort.descending
    by_id = sorted(todos, key=lambda todo: todo.id, reverse=descending)
    if query.sort.field is TodoSortField.CREATED_AT:
        return sorted(by_id, key=lambda todo: todo.created_at, reverse=descending)
    dated = sorted(
        (todo for todo in by_id if todo.due_date is not None),
        key=lambda todo: todo.due_date or date.min,
        reverse=descending,
    )
    return dated + [todo for todo in by_id if todo.due_date is None]
