from dataclasses import dataclass
from uuid import UUID

from todo_api.shared.clock import Clock
from todo_api.todos.application.ports import TodoRepository
from todo_api.todos.application.versioned_write import save
from todo_api.todos.domain.todo import TodoChanges, TodoItem


@dataclass(frozen=True, slots=True)
class UpdateTodoCommand:
    owner_id: str
    todo_id: UUID
    expected_version: int
    changes: TodoChanges


class UpdateTodoHandler:
    def __init__(self, todos: TodoRepository, clock: Clock) -> None:
        self._todos = todos
        self._clock = clock

    async def handle(self, command: UpdateTodoCommand) -> TodoItem:
        return await save(
            self._todos,
            command.owner_id,
            command.todo_id,
            command.expected_version,
            lambda todo: todo.apply(command.changes, self._clock.now()),
        )
