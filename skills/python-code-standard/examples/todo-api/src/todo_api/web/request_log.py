import logging
import time

from starlette.types import ASGIApp, Message, Receive, Scope, Send

logger = logging.getLogger("todo_api.http")

_QUIET_PREFIXES = ("/health/",)


class RequestLogMiddleware:
    """One `http.request` line per request: route template, status, duration. Never the raw path — it is
    attacker-controlled (newlines, ANSI escapes, unbounded length) and explodes log cardinality.
    """

    def __init__(self, app: ASGIApp) -> None:
        self._app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or scope["path"].startswith(_QUIET_PREFIXES):
            await self._app(scope, receive, send)
            return
        started = time.perf_counter()
        status = 500

        async def capture_status(message: Message) -> None:
            nonlocal status
            if message["type"] == "http.response.start":
                status = message["status"]
            await send(message)

        try:
            await self._app(scope, receive, capture_status)
        finally:
            route = getattr(scope.get("route"), "path", None) or "<unmatched>"
            logger.info(
                "http.request",
                extra={
                    "method": scope["method"],
                    "route": route,
                    "status": status,
                    "duration_ms": round((time.perf_counter() - started) * 1000, 1),
                },
            )
