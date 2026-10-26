import uuid
from dataclasses import dataclass

from todo_api.shared.clock import Clock
from todo_api.todos.application import audit_log
from todo_api.todos.application.ports import TodoRepository
from todo_api.todos.domain.todo import TodoDraft, TodoItem


@dataclass(frozen=True, slots=True)
class CreateTodoCommand:
    owner_id: str
    draft: TodoDraft


class CreateTodoHandler:
    def __init__(self, todos: TodoRepository, clock: Clock) -> None:
        self._todos = todos
        self._clock = clock

    async def handle(self, command: CreateTodoCommand) -> TodoItem:
        todo = TodoItem.create(
            todo_id=uuid.uuid7(),
            owner_id=command.owner_id,
            draft=command.draft,
            now=self._clock.now(),
        )
        await self._todos.add(todo)
        audit_log.todo_created(todo.id, todo.owner_id)
        return todo
