from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from todo_api.container import build_container
from todo_api.infrastructure.observability import configure_logging, configure_telemetry, instrument, uninstrument
from todo_api.settings import Settings
from todo_api.shared.clock import Clock
from todo_api.todos.http.router import router as todos_router
from todo_api.web.auth import TokenSettings, TokenVerifier
from todo_api.web.body_limit import BodyLimitMiddleware
from todo_api.web.exception_handlers import install_exception_handlers
from todo_api.web.health import health_router
from todo_api.web.rate_limit import WriteRateLimiter
from todo_api.web.request_log import RequestLogMiddleware


def create_app(settings: Settings | None = None, *, clock: Clock | None = None) -> FastAPI:
    """Composition root. Run with `uvicorn todo_api.main:create_app --factory`."""
    settings = settings or Settings()
    configure_logging(settings.log_format, settings.log_level)
    telemetry = configure_telemetry()
    container = build_container(settings, clock)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        yield
        uninstrument(app)
        await container.aclose()
        telemetry.flush()

    docs = settings.docs_enabled
    app = FastAPI(
        title="Todo API",
        version="1.0.0",
        lifespan=lifespan,
        openapi_url="/openapi.json" if docs else None,
        docs_url="/docs" if docs else None,
        redoc_url=None,
    )
    app.state.container = container
    app.state.token_verifier = TokenVerifier(
        TokenSettings(
            issuer=settings.auth.issuer,
            audience=settings.auth.audience,
            algorithms=settings.auth.algorithms,
            jwks_url=str(settings.auth.jwks_url) if settings.auth.jwks_url else None,
            public_key_file=settings.auth.public_key_file,
        )
    )
    app.state.write_limiter = WriteRateLimiter(settings.write_rate_limit)

    install_exception_handlers(app)
    app.add_middleware(BodyLimitMiddleware, max_bytes=settings.max_body_bytes)
    app.add_middleware(RequestLogMiddleware)
    app.include_router(health_router(container.readiness_checks(), timeout=settings.readiness_timeout_seconds))
    app.include_router(todos_router)
    instrument(app)
    return app
