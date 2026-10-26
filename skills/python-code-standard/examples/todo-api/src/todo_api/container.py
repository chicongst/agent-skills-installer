from collections.abc import Mapping
from dataclasses import dataclass
from functools import partial

from sqlalchemy.ext.asyncio import AsyncEngine

from todo_api.infrastructure.database import create_engine, create_session_factory, ping
from todo_api.settings import MemoryStorage, Settings
from todo_api.shared.clock import Clock, SystemClock
from todo_api.todos.application.ports import TodoRepository
from todo_api.todos.infrastructure.in_memory_repository import InMemoryTodoRepository
from todo_api.todos.infrastructure.sql_repository import SqlTodoRepository
from todo_api.web.health import ReadinessCheck


@dataclass(frozen=True, slots=True)
class Container:
    """Process-wide singletons. Handlers are cheap and built per request from these in `todos/http/dependencies.py`."""

    clock: Clock
    todos: TodoRepository
    engine: AsyncEngine | None

    def readiness_checks(self) -> Mapping[str, ReadinessCheck]:
        return {} if self.engine is None else {"database": partial(ping, self.engine)}

    async def aclose(self) -> None:
        if self.engine is not None:
            await self.engine.dispose()


def build_container(settings: Settings, clock: Clock | None = None) -> Container:
    clock = clock or SystemClock()
    if isinstance(settings.storage, MemoryStorage):
        return Container(clock=clock, todos=InMemoryTodoRepository(), engine=None)
    engine = create_engine(settings.storage)
    return Container(clock=clock, todos=SqlTodoRepository(create_session_factory(engine)), engine=engine)
