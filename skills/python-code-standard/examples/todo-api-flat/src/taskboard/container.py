from collections.abc import Mapping
from dataclasses import dataclass

from taskboard.settings import Settings
from taskboard.shared.clock import Clock, SystemClock
from taskboard.todos.ports import TodoRepository
from taskboard.todos.repository import InMemoryTodoRepository
from taskboard.web.health import ReadinessCheck


@dataclass(frozen=True, slots=True)
class Container:
    """Process-wide singletons. The service is cheap and built per request in `todos/dependencies.py`."""

    clock: Clock
    todos: TodoRepository

    def readiness_checks(self) -> Mapping[str, ReadinessCheck]:
        return {}

    async def aclose(self) -> None:
        return


def build_container(settings: Settings, clock: Clock | None = None) -> Container:
    """`settings.storage` has a single variant today; a database adds a `match` on its type here."""
    del settings
    return Container(clock=clock or SystemClock(), todos=InMemoryTodoRepository())
