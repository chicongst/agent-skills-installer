from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta

from taskboard.todos.domain import TodoItem
from taskboard.todos.ports import Stale, WriteResult
from taskboard.todos.repository import InMemoryTodoRepository


@dataclass
class FixedClock:
    current: datetime = field(default_factory=lambda: datetime(2026, 1, 1, 9, 0, tzinfo=UTC))

    def now(self) -> datetime:
        return self.current

    def advance(self, **delta: float) -> None:
        self.current += timedelta(**delta)


class RacingTodoRepository(InMemoryTodoRepository):
    """The real in-memory adapter, plus a hook that makes the next update lose a race after the service loaded."""

    def __init__(self) -> None:
        super().__init__()
        self.updates = 0
        self.lose_next_update_to: int | None = None

    async def update(self, todo: TodoItem, expected_version: int) -> WriteResult:
        if self.lose_next_update_to is not None:
            current, self.lose_next_update_to = self.lose_next_update_to, None
            return Stale(current)
        self.updates += 1
        return await super().update(todo, expected_version)
