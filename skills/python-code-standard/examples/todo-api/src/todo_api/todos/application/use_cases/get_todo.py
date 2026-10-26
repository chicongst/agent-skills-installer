from dataclasses import dataclass
from uuid import UUID

from todo_api.todos.application.ports import TodoRepository
from todo_api.todos.domain.errors import TodoNotFoundError
from todo_api.todos.domain.todo import TodoItem


@dataclass(frozen=True, slots=True)
class GetTodoQuery:
    owner_id: str
    todo_id: UUID


class GetTodoHandler:
    def __init__(self, todos: TodoRepository) -> None:
        self._todos = todos

    async def handle(self, query: GetTodoQuery) -> TodoItem:
        todo = await self._todos.get(query.owner_id, query.todo_id)
        if todo is None:
            raise TodoNotFoundError(query.todo_id)
        return todo
