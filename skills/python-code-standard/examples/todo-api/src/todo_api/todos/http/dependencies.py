from typing import Annotated, Protocol

from fastapi import Depends, Request

from todo_api.shared.clock import Clock
from todo_api.todos.application.ports import TodoRepository
from todo_api.todos.application.use_cases.complete_todo import CompleteTodoHandler
from todo_api.todos.application.use_cases.create_todo import CreateTodoHandler
from todo_api.todos.application.use_cases.delete_todo import DeleteTodoHandler
from todo_api.todos.application.use_cases.get_todo import GetTodoHandler
from todo_api.todos.application.use_cases.list_todos import ListTodosHandler
from todo_api.todos.application.use_cases.reopen_todo import ReopenTodoHandler
from todo_api.todos.application.use_cases.update_todo import UpdateTodoHandler


class TodoServices(Protocol):
    """What this feature needs from the composition root (`todo_api.container.Container` satisfies it)."""

    @property
    def clock(self) -> Clock: ...

    @property
    def todos(self) -> TodoRepository: ...


def _services(request: Request) -> TodoServices:
    services: TodoServices = request.app.state.container
    return services


ContainerDep = Annotated[TodoServices, Depends(_services)]


def _create(c: ContainerDep) -> CreateTodoHandler:
    return CreateTodoHandler(c.todos, c.clock)


def _get(c: ContainerDep) -> GetTodoHandler:
    return GetTodoHandler(c.todos)


def _list(c: ContainerDep) -> ListTodosHandler:
    return ListTodosHandler(c.todos)


def _update(c: ContainerDep) -> UpdateTodoHandler:
    return UpdateTodoHandler(c.todos, c.clock)


def _complete(c: ContainerDep) -> CompleteTodoHandler:
    return CompleteTodoHandler(c.todos, c.clock)


def _reopen(c: ContainerDep) -> ReopenTodoHandler:
    return ReopenTodoHandler(c.todos, c.clock)


def _delete(c: ContainerDep) -> DeleteTodoHandler:
    return DeleteTodoHandler(c.todos)


CreateHandler = Annotated[CreateTodoHandler, Depends(_create)]
GetHandler = Annotated[GetTodoHandler, Depends(_get)]
ListHandler = Annotated[ListTodosHandler, Depends(_list)]
UpdateHandler = Annotated[UpdateTodoHandler, Depends(_update)]
CompleteHandler = Annotated[CompleteTodoHandler, Depends(_complete)]
ReopenHandler = Annotated[ReopenTodoHandler, Depends(_reopen)]
DeleteHandler = Annotated[DeleteTodoHandler, Depends(_delete)]
