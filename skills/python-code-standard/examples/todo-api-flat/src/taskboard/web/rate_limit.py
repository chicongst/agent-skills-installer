import math
import time

from fastapi import Request
from limits import RateLimitItem, parse
from limits.aio.storage import MemoryStorage
from limits.aio.strategies import MovingWindowRateLimiter

from taskboard.web.auth import CurrentOwner
from taskboard.web.problems import ProblemError


class WriteRateLimiter:
    """Per-user moving window. Memory storage makes the limit per replica; a shared storage URI changes that."""

    def __init__(self, limit: str) -> None:
        self._item: RateLimitItem = parse(limit)
        self._limiter = MovingWindowRateLimiter(MemoryStorage())

    async def hit(self, owner_id: str) -> None:
        if await self._limiter.hit(self._item, "writes", owner_id):
            return
        stats = await self._limiter.get_window_stats(self._item, "writes", owner_id)
        retry_after = max(1, math.ceil(stats.reset_time - time.time()))
        raise ProblemError(429, "Too many writes; slow down.", headers={"Retry-After": str(retry_after)})


async def limit_writes(request: Request, owner_id: CurrentOwner) -> None:
    limiter: WriteRateLimiter = request.app.state.write_limiter
    await limiter.hit(owner_id)
