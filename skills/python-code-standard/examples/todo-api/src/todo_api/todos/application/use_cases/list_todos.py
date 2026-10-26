from todo_api.shared.pagination import Page
from todo_api.todos.application.ports import TodoListQuery, TodoRepository
from todo_api.todos.domain.todo import TodoItem


class ListTodosHandler:
    def __init__(self, todos: TodoRepository) -> None:
        self._todos = todos

    async def handle(self, query: TodoListQuery) -> Page[TodoItem]:
        return await self._todos.list(query)
