import uuid
from datetime import date

import pytest

from tests.fakes import FixedClock
from todo_api.shared.patch import UNSET
from todo_api.todos.domain.errors import TodoValidationError
from todo_api.todos.domain.todo import TITLE_MAX_LENGTH, TodoChanges, TodoDraft, TodoItem, TodoPriority, TodoStatus

CLOCK = FixedClock()


def make(**draft: object) -> TodoItem:
    return TodoItem.create(
        todo_id=uuid.uuid7(),
        owner_id="user-alex",
        draft=TodoDraft(**{"title": "Buy milk", **draft}),  # type: ignore[arg-type]
        now=CLOCK.now(),
    )


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


def test_apply_changes_only_sent_fields_and_bumps_version() -> None:
    todo = make(description="2 litres", due_date=date(2026, 2, 1))

    changed = todo.apply(TodoChanges(description=None, priority=TodoPriority.HIGH), CLOCK.now())

    assert (changed.title, changed.description, changed.due_date) == ("Buy milk", None, date(2026, 2, 1))
    assert (changed.priority, changed.version) == (TodoPriority.HIGH, 2)


def test_apply_null_title_raises() -> None:
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


@pytest.mark.parametrize("field", ["title", "description"])
@pytest.mark.parametrize("text", ["a\x00b", "\u200b", "\x1b[31mred", "a\u202eb"])
def test_control_and_invisible_characters_are_rejected(field: str, text: str) -> None:
    with pytest.raises(TodoValidationError) as error:
        make(**{field: text})

    assert error.value.field == field


def test_description_keeps_newlines_and_tabs() -> None:
    assert make(description="line 1\n\tline 2").description == "line 1\n\tline 2"


def test_complete_then_complete_again_is_a_no_op() -> None:
    done = make().complete(CLOCK.now())

    assert (done.status, done.completed_at, done.version) == (TodoStatus.DONE, CLOCK.now(), 2)
    assert done.complete(CLOCK.now()) is done


def test_reopen_clears_completed_at() -> None:
    reopened = make().complete(CLOCK.now()).reopen(CLOCK.now())

    assert (reopened.status, reopened.completed_at, reopened.version) == (TodoStatus.OPEN, None, 3)
