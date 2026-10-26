from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from taskboard.container import build_container
from taskboard.infrastructure.observability import configure_logging, configure_telemetry, instrument, uninstrument
from taskboard.settings import Settings
from taskboard.shared.clock import Clock
from taskboard.todos.router import router as todos_router
from taskboard.web.auth import TokenSettings, TokenVerifier
from taskboard.web.body_limit import BodyLimitMiddleware
from taskboard.web.exception_handlers import install_exception_handlers
from taskboard.web.health import health_router
from taskboard.web.rate_limit import WriteRateLimiter
from taskboard.web.request_log import RequestLogMiddleware


def create_app(settings: Settings | None = None, *, clock: Clock | None = None) -> FastAPI:
    """Composition root. Run with `uvicorn taskboard.main:create_app --factory`."""
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
        title="Taskboard API",
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
