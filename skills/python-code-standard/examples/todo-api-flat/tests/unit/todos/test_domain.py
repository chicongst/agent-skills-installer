import uuid
from datetime import date

import pytest

from taskboard.shared.patch import UNSET
from taskboard.todos.domain import (
    TITLE_MAX_LENGTH,
    TodoChanges,
    TodoDraft,
    TodoItem,
    TodoPriority,
    TodoStatus,
    TodoValidationError,
)
from tests.fakes import FixedClock

CLOCK = FixedClock()


def make(
    title: str = "Buy milk",
    description: str | None = None,
    due_date: date | None = None,
    priority: TodoPriority | None = None,
) -> TodoItem:
    draft = TodoDraft(title=title, description=description, due_date=due_date, priority=priority)
    return TodoItem.create(todo_id=uuid.uuid7(), owner_id="user-alex", draft=draft, now=CLOCK.now())


def test_create_trims_and_starts_open_at_version_1() -> None:
    todo = make(title="  Buy milk  ", description="   ")

    assert (todo.title, todo.description, todo.status, todo.version) == ("Buy milk", None, TodoStatus.OPEN, 1)
    assert todo.created_at == todo.updated_at == CLOCK.now()


@pytest.mark.parametrize(("title", "message"), [("   ", "required"), ("x" * (TITLE_MAX_LENGTH + 1), "at most")])
def test_create_invalid_title_raises_field_error(title: str, message: str) -> None:
    with pytest.raises(TodoValidationError) as error:
        make(title=title)

    assert error.value.field == "title"
    assert message in error.value.message


def test_create_blank_owner_raises() -> None:
    with pytest.raises(TodoValidationError):
        TodoItem.create(todo_id=uuid.uuid7(), owner_id=" ", draft=TodoDraft(title="x"), now=CLOCK.now())


def test_apply_sent_fields_only_changes_those_and_bumps_version() -> None:
    todo = make(description="2 litres", due_date=date(2026, 2, 1))

    changed = todo.apply(TodoChanges(description=None, priority=TodoPriority.HIGH), CLOCK.now())

    assert (changed.title, changed.description, changed.due_date) == ("Buy milk", None, date(2026, 2, 1))
    assert (changed.priority, changed.version) == (TodoPriority.HIGH, 2)


def test_apply_null_title_raises_for_title() -> None:
    with pytest.raises(TodoValidationError) as error:
        make().apply(TodoChanges(title=None), CLOCK.now())

    assert error.value.field == "title"


def test_apply_nothing_raises_for_the_whole_request() -> None:
    with pytest.raises(TodoValidationError) as error:
        make().apply(TodoChanges(title=UNSET), CLOCK.now())

    assert error.value.field is None


def test_apply_values_equal_to_current_returns_the_same_instance() -> None:
    todo = make(priority=TodoPriority.LOW)

    assert todo.apply(TodoChanges(title=" Buy milk ", priority=TodoPriority.LOW), CLOCK.now()) is todo


@pytest.mark.parametrize("text", ["\u200b", "\x1b[31mred", "a\u202eb"])
def test_create_invisible_or_control_characters_in_title_raise(text: str) -> None:
    with pytest.raises(TodoValidationError) as error:
        make(title=text)

    assert error.value.field == "title"


def test_description_keeps_newlines_and_tabs() -> None:
    assert make(description="line 1\n\tline 2").description == "line 1\n\tline 2"


def test_create_nul_character_in_title_raises_for_title() -> None:
    with pytest.raises(TodoValidationError) as error:
        make(title="a\x00b")

    assert error.value.field == "title"


def test_create_nul_character_in_description_raises_for_description() -> None:
    with pytest.raises(TodoValidationError) as error:
        make(description="a\x00b")

    assert error.value.field == "description"


def test_complete_twice_second_call_returns_same_instance() -> None:
    done = make().complete(CLOCK.now())

    assert (done.status, done.completed_at, done.version) == (TodoStatus.DONE, CLOCK.now(), 2)
    assert done.complete(CLOCK.now()) is done


def test_reopen_done_todo_clears_completed_at() -> None:
    reopened = make().complete(CLOCK.now()).reopen(CLOCK.now())

    assert (reopened.status, reopened.completed_at, reopened.version) == (TodoStatus.OPEN, None, 3)


def test_reopen_open_todo_returns_same_instance() -> None:
    todo = make()

    assert todo.reopen(CLOCK.now()) is todo
