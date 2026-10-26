from starlette.types import ASGIApp, Message, Receive, Scope, Send

from todo_api.web.problems import ProblemError, from_error


class BodyLimitMiddleware:
    """Uvicorn has no body size limit. Reject by Content-Length up front, then count streamed chunks."""

    def __init__(self, app: ASGIApp, *, max_bytes: int) -> None:
        self._app = app
        self._max_bytes = max_bytes

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self._app(scope, receive, send)
            return
        limit = self._max_bytes
        declared = dict(scope["headers"]).get(b"content-length", b"")
        if declared.isdigit() and int(declared) > limit:
            await from_error(_too_large(limit))(scope, receive, send)
            return
        received = 0

        async def limited_receive() -> Message:
            nonlocal received
            message = await receive()
            if message["type"] == "http.request":
                received += len(message.get("body", b""))
                if received > limit:
                    raise _too_large(limit)
            return message

        await self._app(scope, limited_receive, send)


def _too_large(limit: int) -> ProblemError:
    return ProblemError(413, f"Request body must be at most {limit} bytes.")
