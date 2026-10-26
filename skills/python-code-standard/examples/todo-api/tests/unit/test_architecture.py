import dataclasses

from fastapi.dependencies.models import Dependant
from fastapi.routing import APIRoute

from todo_api.todos.domain.todo import TodoItem
from todo_api.todos.http.router import router as todos_router
from todo_api.todos.infrastructure.tables import COLUMNS
from todo_api.web.auth import current_owner


def _calls(dependant: Dependant) -> set[object]:
    calls: set[object] = {dependant.call}
    for child in dependant.dependencies:
        calls |= _calls(child)
    return calls


def test_every_todo_route_requires_an_authenticated_owner() -> None:
    routes = [route for route in todos_router.routes if isinstance(route, APIRoute)]

    unprotected = [route.path for route in routes if current_owner not in _calls(route.dependant)]

    assert len(routes) == 7
    assert unprotected == []


def test_table_columns_match_the_aggregate_exactly() -> None:
    assert set(COLUMNS) == {field.name for field in dataclasses.fields(TodoItem)}
