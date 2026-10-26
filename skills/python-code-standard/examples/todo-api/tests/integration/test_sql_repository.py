import asyncio
import uuid
from collections.abc import AsyncIterator
from datetime import UTC, date, datetime

import pytest
from pydantic import SecretStr
from sqlalchemy.ext.asyncio import AsyncEngine

from todo_api.infrastructure.database import create_engine, create_session_factory
from todo_api.settings import PostgresStorage
from todo_api.todos.application.ports import Missing, Stale, Written
from todo_api.todos.domain.todo import TodoChanges, TodoDraft, TodoItem, TodoPriority
from todo_api.todos.infrastructure.sql_repository import SqlTodoRepository

pytestmark = pytest.mark.postgres

NOW = datetime(2026, 1, 1, 9, 0, tzinfo=UTC)


@pytest.fixture
async def engine(postgres_url: str) -> AsyncIterator[AsyncEngine]:
    engine = create_engine(PostgresStorage(driver="postgres", database_url=SecretStr(postgres_url)))
    yield engine
    await engine.dispose()


@pytest.fixture
def repo(engine: AsyncEngine) -> SqlTodoRepository:
    return SqlTodoRepository(create_session_factory(engine))


def new_todo(owner: str = "user-alex") -> TodoItem:
    draft = TodoDraft(title="Buy milk", description="2 litres", due_date=date(2026, 2, 1), priority=TodoPriority.LOW)
    return TodoItem.create(todo_id=uuid.uuid7(), owner_id=f"{owner}-{uuid.uuid4().hex}", draft=draft, now=NOW)


async def test_every_column_round_trips_on_insert_and_update(repo: SqlTodoRepository) -> None:
    todo = new_todo()
    await repo.add(todo)
    changed = todo.apply(TodoChanges(title="Buy oat milk", priority=None), NOW).complete(NOW)

    result = await repo.update(changed, expected_version=1)

    assert result == Written()
    assert await repo.get(todo.owner_id, todo.id) == changed


async def test_two_writers_with_the_same_version_one_wins_one_gets_current(repo: SqlTodoRepository) -> None:
    todo = new_todo()
    await repo.add(todo)

    results = await asyncio.gather(
        repo.update(todo.apply(TodoChanges(title="A"), NOW), expected_version=1),
        repo.update(todo.apply(TodoChanges(title="B"), NOW), expected_version=1),
    )

    assert sorted(results, key=repr) == [Stale(2), Written()]


async def test_another_owner_cannot_update_or_delete(repo: SqlTodoRepository) -> None:
    todo = new_todo()
    await repo.add(todo)
    intruder = TodoItem.create(todo_id=todo.id, owner_id="user-sam", draft=TodoDraft(title="Mine now"), now=NOW)

    assert await repo.update(intruder, expected_version=1) == Missing()
    assert await repo.delete("user-sam", todo.id, expected_version=1) == Missing()
    assert await repo.get(todo.owner_id, todo.id) == todo
