import logging
import uuid
from collections.abc import Callable
from typing import assert_never
from uuid import UUID

from taskboard.shared.clock import Clock
from taskboard.shared.pagination import Page
from taskboard.todos.domain import (
    TodoChanges,
    TodoDraft,
    TodoItem,
    TodoNotFoundError,
    VersionMismatchError,
)
from taskboard.todos.ports import Missing, Stale, TodoListQuery, TodoRepository, WriteResult, Written

logger = logging.getLogger("taskboard.todos")


class TodoService:
    """All todo use cases. Every write is guarded by the version the caller last read (ADR-002)."""

    def __init__(self, todos: TodoRepository, clock: Clock) -> None:
        self._todos = todos
        self._clock = clock

    async def create(self, owner_id: str, draft: TodoDraft) -> TodoItem:
        todo = TodoItem.create(todo_id=uuid.uuid7(), owner_id=owner_id, draft=draft, now=self._clock.now())
        await self._todos.add(todo)
        logger.info("todo.created", extra={"todo_id": str(todo.id), "owner_id": owner_id})
        return todo

    async def get(self, owner_id: str, todo_id: UUID) -> TodoItem:
        todo = await self._todos.get(owner_id, todo_id)
        if todo is None:
            raise TodoNotFoundError(todo_id)
        return todo

    async def list(self, query: TodoListQuery) -> Page[TodoItem]:
        return await self._todos.list(query)

    async def update(self, owner_id: str, todo_id: UUID, expected_version: int, changes: TodoChanges) -> TodoItem:
        return await self._save(owner_id, todo_id, expected_version, lambda t: t.apply(changes, self._clock.now()))

    async def complete(self, owner_id: str, todo_id: UUID, expected_version: int) -> TodoItem:
        return await self._save(owner_id, todo_id, expected_version, lambda t: t.complete(self._clock.now()))

    async def reopen(self, owner_id: str, todo_id: UUID, expected_version: int) -> TodoItem:
        return await self._save(owner_id, todo_id, expected_version, lambda t: t.reopen(self._clock.now()))

    async def delete(self, owner_id: str, todo_id: UUID, expected_version: int) -> None:
        _raise_for(await self._todos.delete(owner_id, todo_id, expected_version), todo_id, expected_version)
        logger.info("todo.deleted", extra={"todo_id": str(todo_id), "owner_id": owner_id})

    async def _save(
        self, owner_id: str, todo_id: UUID, expected_version: int, change: Callable[[TodoItem], TodoItem]
    ) -> TodoItem:
        """Checking the version before the domain change answers 412 for a stale ETag even when the change
        would be a no-op; the guarded write then catches a writer that slipped in after the load."""
        current = await self.get(owner_id, todo_id)
        if current.version != expected_version:
            _log_conflict(todo_id, expected_version, current.version)
            raise VersionMismatchError(current.version)
        changed = change(current)
        if changed is current:
            return current
        _raise_for(await self._todos.update(changed, expected_version), todo_id, expected_version)
        return changed


def _raise_for(result: WriteResult, todo_id: UUID, expected_version: int) -> None:
    match result:
        case Written():
            return
        case Missing():
            raise TodoNotFoundError(todo_id)
        case Stale(current_version=current_version):
            _log_conflict(todo_id, expected_version, current_version)
            raise VersionMismatchError(current_version)
        case _:
            assert_never(result)


def _log_conflict(todo_id: UUID, expected_version: int, current_version: int) -> None:
    logger.warning(
        "todo.version_conflict",
        extra={"todo_id": str(todo_id), "expected_version": expected_version, "current_version": current_version},
    )
