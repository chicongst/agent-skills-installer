from collections.abc import Sequence
from dataclasses import dataclass

DEFAULT_LIMIT = 20
MAX_LIMIT = 100
MAX_OFFSET = 10_000


@dataclass(frozen=True, slots=True)
class PageRequest:
    limit: int = DEFAULT_LIMIT
    offset: int = 0


@dataclass(frozen=True, slots=True)
class Page[T]:
    items: Sequence[T]
    total: int
    limit: int
    offset: int
