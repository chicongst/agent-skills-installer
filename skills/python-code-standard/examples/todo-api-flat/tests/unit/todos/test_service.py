import uuid

import pytest

from taskboard.todos.domain import TodoChanges, TodoDraft, TodoItem, TodoNotFoundError, VersionMismatchError
from taskboard.todos.service import TodoService
from tests.fakes import FixedClock, RacingTodoRepository

OWNER = "user-alex"


@pytest.fixture
def clock() -> FixedClock:
    return FixedClock()


@pytest.fixture
def repo() -> RacingTodoRepository:
    return RacingTodoRepository()


@pytest.fixture
def service(repo: RacingTodoRepository, clock: FixedClock) -> TodoService:
    return TodoService(repo, clock)


async def created(service: TodoService) -> TodoItem:
    return await service.create(OWNER, TodoDraft(title="Buy milk"))


async def test_update_with_current_version_saves_next_version(
    service: TodoService, repo: RacingTodoRepository, clock: FixedClock
) -> None:
    todo = await created(service)
    clock.advance(minutes=5)

    updated = await service.update(OWNER, todo.id, 1, TodoChanges(title="Buy oat milk"))

    assert (updated.title, updated.version, updated.updated_at) == ("Buy oat milk", 2, clock.now())
    assert await repo.get(OWNER, todo.id) == updated


async def test_update_with_old_version_reports_current_without_writing(
    service: TodoService, repo: RacingTodoRepository
) -> None:
    todo = await created(service)

    with pytest.raises(VersionMismatchError) as error:
        await service.update(OWNER, todo.id, 7, TodoChanges(title="x"))

    assert error.value.details == {"current_version": 1}
    assert repo.updates == 0


async def test_update_losing_the_race_after_load_raises_mismatch(
    service: TodoService, repo: RacingTodoRepository
) -> None:
    todo = await created(service)
    repo.lose_next_update_to = 2

    with pytest.raises(VersionMismatchError) as error:
        await service.update(OWNER, todo.id, 1, TodoChanges(title="x"))

    assert error.value.details == {"current_version": 2}


async def test_update_with_unchanged_values_does_not_write(service: TodoService, repo: RacingTodoRepository) -> None:
    todo = await created(service)

    same = await service.update(OWNER, todo.id, 1, TodoChanges(title="Buy milk"))

    assert (same, repo.updates) == (todo, 0)


async def test_update_another_owners_todo_raises_not_found(service: TodoService) -> None:
    todo = await created(service)

    with pytest.raises(TodoNotFoundError):
        await service.update("user-sam", todo.id, 1, TodoChanges(title="x"))


async def test_complete_already_done_does_not_write(service: TodoService, repo: RacingTodoRepository) -> None:
    todo = await created(service)
    await service.complete(OWNER, todo.id, 1)

    again = await service.complete(OWNER, todo.id, 2)

    assert (again.version, repo.updates) == (2, 1)


async def test_delete_unknown_todo_raises_not_found(service: TodoService) -> None:
    with pytest.raises(TodoNotFoundError):
        await service.delete(OWNER, uuid.uuid7(), 1)


async def test_delete_with_stale_version_raises_mismatch_and_keeps_todo(
    service: TodoService, repo: RacingTodoRepository
) -> None:
    todo = await created(service)

    with pytest.raises(VersionMismatchError):
        await service.delete(OWNER, todo.id, 2)

    assert await repo.get(OWNER, todo.id) == todo
