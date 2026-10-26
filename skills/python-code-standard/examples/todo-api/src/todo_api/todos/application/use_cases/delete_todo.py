from dataclasses import dataclass
from uuid import UUID

from todo_api.todos.application import audit_log
from todo_api.todos.application.ports import TodoRepository
from todo_api.todos.application.versioned_write import raise_for


@dataclass(frozen=True, slots=True)
class DeleteTodoCommand:
    owner_id: str
    todo_id: UUID
    expected_version: int


class DeleteTodoHandler:
    def __init__(self, todos: TodoRepository) -> None:
        self._todos = todos

    async def handle(self, command: DeleteTodoCommand) -> None:
        result = await self._todos.delete(command.owner_id, command.todo_id, command.expected_version)
        raise_for(result, command.todo_id, command.expected_version)
        audit_log.todo_deleted(command.todo_id, command.owner_id)
