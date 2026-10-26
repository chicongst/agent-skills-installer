from collections.abc import Callable
from typing import assert_never
from uuid import UUID

from todo_api.todos.application import audit_log
from todo_api.todos.application.ports import Missing, Stale, TodoRepository, WriteResult, Written
from todo_api.todos.domain.errors import TodoNotFoundError, VersionMismatchError
from todo_api.todos.domain.todo import TodoItem


async def save(
    todos: TodoRepository,
    owner_id: str,
    todo_id: UUID,
    expected_version: int,
    change: Callable[[TodoItem], TodoItem],
) -> TodoItem:
    """Load, check the caller's version, apply a pure domain change, and write it back guarded by that version."""
    current = await todos.get(owner_id, todo_id)
    if current is None:
        raise TodoNotFoundError(todo_id)
    if current.version != expected_version:
        audit_log.version_conflict(todo_id, expected_version, current.version)
        raise VersionMismatchError(current.version)
    changed = change(current)
    if changed is current:
        return current
    raise_for(await todos.update(changed, expected_version), todo_id, expected_version)
    return changed


def raise_for(result: WriteResult, todo_id: UUID, expected_version: int) -> None:
    match result:
        case Written():
            return
        case Missing():
            raise TodoNotFoundError(todo_id)
        case Stale(current_version=current_version):
            audit_log.version_conflict(todo_id, expected_version, current_version)
            raise VersionMismatchError(current_version)
        case _:
            assert_never(result)
