from typing import Annotated, Protocol

from fastapi import Depends, Request

from taskboard.shared.clock import Clock
from taskboard.todos.ports import TodoRepository
from taskboard.todos.service import TodoService


class TodoServices(Protocol):
    """What this feature needs from the composition root (`taskboard.container.Container` satisfies it)."""

    @property
    def clock(self) -> Clock: ...

    @property
    def todos(self) -> TodoRepository: ...


def _services(request: Request) -> TodoServices:
    services: TodoServices = request.app.state.container
    return services


def _todo_service(services: Annotated[TodoServices, Depends(_services)]) -> TodoService:
    return TodoService(services.todos, services.clock)


Todos = Annotated[TodoService, Depends(_todo_service)]
