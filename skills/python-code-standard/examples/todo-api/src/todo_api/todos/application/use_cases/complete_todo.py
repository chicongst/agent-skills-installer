from dataclasses import dataclass
from uuid import UUID

from todo_api.shared.clock import Clock
from todo_api.todos.application.ports import TodoRepository
from todo_api.todos.application.versioned_write import save
from todo_api.todos.domain.todo import TodoItem


@dataclass(frozen=True, slots=True)
class CompleteTodoCommand:
    owner_id: str
    todo_id: UUID
    expected_version: int


class CompleteTodoHandler:
    def __init__(self, todos: TodoRepository, clock: Clock) -> None:
        self._todos = todos
        self._clock = clock

    async def handle(self, command: CompleteTodoCommand) -> TodoItem:
        return await save(
            self._todos,
            command.owner_id,
            command.todo_id,
            command.expected_version,
            lambda todo: todo.complete(self._clock.now()),
        )
