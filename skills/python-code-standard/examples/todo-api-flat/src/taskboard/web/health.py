import asyncio
import logging
from collections.abc import Awaitable, Callable, Mapping

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from taskboard.web.problems import problem

type ReadinessCheck = Callable[[], Awaitable[None]]

logger = logging.getLogger(__name__)


def health_router(checks: Mapping[str, ReadinessCheck], *, timeout: float) -> APIRouter:
    """`/health/live` never touches dependencies (a DB outage must not restart pods); `/health/ready` checks them
    concurrently under one timeout kept below the orchestrator's probe timeout, so the probe sees a 503, not a hang.
    """
    router = APIRouter(prefix="/health", tags=["health"])

    @router.get("/live")
    async def live() -> dict[str, str]:
        return {"status": "ok"}

    @router.get("/ready", response_model=None)
    async def ready() -> dict[str, str] | JSONResponse:
        names = list(checks)
        results = await asyncio.gather(
            *(_bounded(check(), timeout) for check in checks.values()), return_exceptions=True
        )
        failing = [name for name, result in zip(names, results, strict=True) if isinstance(result, BaseException)]
        for name, result in zip(names, results, strict=True):
            if isinstance(result, BaseException):
                logger.warning("health.not_ready", extra={"check": name}, exc_info=result)
        if failing:
            return problem(503, f"Not ready: {', '.join(failing)}.", extra={"failing": failing})
        return {"status": "ok"}

    return router


async def _bounded(pending: Awaitable[None], seconds: float) -> None:
    async with asyncio.timeout(seconds):
        await pending
