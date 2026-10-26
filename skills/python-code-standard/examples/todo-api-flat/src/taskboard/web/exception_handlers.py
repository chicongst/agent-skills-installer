import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic.alias_generators import to_camel
from starlette.exceptions import HTTPException

from taskboard.shared.errors import DomainError, ErrorKind
from taskboard.web.problems import ProblemError, from_error, problem
from taskboard.web.strict_json import InvalidBodyError

logger = logging.getLogger(__name__)

_STATUS_BY_KIND = {
    ErrorKind.VALIDATION: 422,
    ErrorKind.NOT_FOUND: 404,
    ErrorKind.VERSION_MISMATCH: 412,
}


def install_exception_handlers(app: FastAPI) -> None:
    """The only place errors become HTTP: every response is application/problem+json with a stable `code`."""

    @app.exception_handler(DomainError)
    async def domain_error(_: Request, error: DomainError) -> JSONResponse:
        extra: dict[str, object] = {to_camel(key): value for key, value in error.details.items()}
        if error.kind is ErrorKind.VALIDATION:
            extra["errors"] = {to_camel(error.field) if error.field else "body": [error.message]}
        return problem(_STATUS_BY_KIND[error.kind], error.message, code=error.code, extra=extra)

    @app.exception_handler(ProblemError)
    async def problem_error(_: Request, error: ProblemError) -> JSONResponse:
        return from_error(error)

    @app.exception_handler(InvalidBodyError)
    async def invalid_body(_: Request, error: InvalidBodyError) -> JSONResponse:
        return problem(422, "The request body is invalid.", extra={"errors": error.errors})

    @app.exception_handler(RequestValidationError)
    async def request_validation(_: Request, error: RequestValidationError) -> JSONResponse:
        errors: dict[str, list[str]] = {}
        for item in error.errors():
            # An unknown key is reported as sent; camelising `due_date` would point the client at the valid name.
            parts = [str(part) for part in item["loc"]]
            location = parts if item["type"] == "extra_forbidden" else [to_camel(part) for part in parts]
            errors.setdefault(".".join(location[1:]) or location[0], []).append(str(item["msg"]))
        return problem(422, "The request is invalid.", extra={"errors": errors})

    @app.exception_handler(HTTPException)
    async def http_exception(_: Request, error: HTTPException) -> JSONResponse:
        return problem(error.status_code, str(error.detail), headers=error.headers)

    @app.exception_handler(Exception)
    async def unhandled(request: Request, error: Exception) -> JSONResponse:
        logger.error(
            "http.unhandled_exception",
            extra={"path": request.url.path, "method": request.method},
            exc_info=error,
        )
        return problem(500, "An unexpected error occurred.")
