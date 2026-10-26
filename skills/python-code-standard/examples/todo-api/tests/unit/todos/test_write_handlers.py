import uuid

import pytest

from tests.fakes import FixedClock, RacingTodoRepository
from todo_api.todos.application.use_cases.complete_todo import CompleteTodoCommand, CompleteTodoHandler
from todo_api.todos.application.use_cases.create_todo import CreateTodoCommand, CreateTodoHandler
from todo_api.todos.application.use_cases.delete_todo import DeleteTodoCommand, DeleteTodoHandler
from todo_api.todos.application.use_cases.update_todo import UpdateTodoCommand, UpdateTodoHandler
from todo_api.todos.domain.errors import TodoNotFoundError, VersionMismatchError
from todo_api.todos.domain.todo import TodoChanges, TodoDraft, TodoItem

OWNER = "user-alex"


@pytest.fixture
def clock() -> FixedClock:
    return FixedClock()


@pytest.fixture
def repo() -> RacingTodoRepository:
    return RacingTodoRepository()


async def created(repo: RacingTodoRepository, clock: FixedClock) -> TodoItem:
    return await CreateTodoHandler(repo, clock).handle(CreateTodoCommand(OWNER, TodoDraft(title="Buy milk")))


async def test_update_with_current_version_saves_next_version(repo: RacingTodoRepository, clock: FixedClock) -> None:
    todo = await created(repo, clock)
    clock.advance(minutes=5)

    updated = await UpdateTodoHandler(repo, clock).handle(
        UpdateTodoCommand(OWNER, todo.id, 1, TodoChanges(title="Buy oat milk"))
    )

    assert (updated.title, updated.version, updated.updated_at) == ("Buy oat milk", 2, clock.now())
    assert await repo.get(OWNER, todo.id) == updated


async def test_update_with_old_version_reports_current_without_writing(
    repo: RacingTodoRepository, clock: FixedClock
) -> None:
    todo = await created(repo, clock)

    with pytest.raises(VersionMismatchError) as error:
        await UpdateTodoHandler(repo, clock).handle(UpdateTodoCommand(OWNER, todo.id, 7, TodoChanges(title="x")))

    assert error.value.details == {"current_version": 1}
    assert repo.updates == 0


async def test_update_losing_the_race_after_load_raises_mismatch(repo: RacingTodoRepository, clock: FixedClock) -> None:
    todo = await created(repo, clock)
    repo.lose_next_update_to = 2

    with pytest.raises(VersionMismatchError) as error:
        await UpdateTodoHandler(repo, clock).handle(UpdateTodoCommand(OWNER, todo.id, 1, TodoChanges(title="x")))

    assert error.value.details == {"current_version": 2}


async def test_update_with_unchanged_values_does_not_write(repo: RacingTodoRepository, clock: FixedClock) -> None:
    todo = await created(repo, clock)

    same = await UpdateTodoHandler(repo, clock).handle(
        UpdateTodoCommand(OWNER, todo.id, 1, TodoChanges(title="Buy milk"))
    )

    assert (same, repo.updates) == (todo, 0)


async def test_update_another_owners_todo_is_not_found(repo: RacingTodoRepository, clock: FixedClock) -> None:
    todo = await created(repo, clock)

    with pytest.raises(TodoNotFoundError):
        await UpdateTodoHandler(repo, clock).handle(UpdateTodoCommand("user-sam", todo.id, 1, TodoChanges(title="x")))


async def test_complete_already_done_does_not_write(repo: RacingTodoRepository, clock: FixedClock) -> None:
    todo = await created(repo, clock)
    handler = CompleteTodoHandler(repo, clock)
    await handler.handle(CompleteTodoCommand(OWNER, todo.id, 1))

    again = await handler.handle(CompleteTodoCommand(OWNER, todo.id, 2))

    assert (again.version, repo.updates) == (2, 1)


async def test_delete_unknown_todo_is_not_found(repo: RacingTodoRepository) -> None:
    with pytest.raises(TodoNotFoundError):
        await DeleteTodoHandler(repo).handle(DeleteTodoCommand(OWNER, uuid.uuid7(), 1))
