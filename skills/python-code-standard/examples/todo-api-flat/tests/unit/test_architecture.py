from fastapi.dependencies.models import Dependant
from fastapi.routing import APIRoute

from taskboard.todos.router import router as todos_router
from taskboard.web.auth import current_owner


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
