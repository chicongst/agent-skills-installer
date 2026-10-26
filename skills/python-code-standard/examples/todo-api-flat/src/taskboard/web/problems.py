from collections.abc import Mapping
from http import HTTPStatus
from typing import Any

from fastapi.responses import JSONResponse
from opentelemetry import trace
from pydantic import BaseModel, Field

PROBLEM_JSON = "application/problem+json"

CODES: Mapping[int, str] = {
    400: "BAD_REQUEST",
    401: "UNAUTHORIZED",
    403: "FORBIDDEN",
    404: "NOT_FOUND",
    405: "METHOD_NOT_ALLOWED",
    412: "VERSION_MISMATCH",
    413: "PAYLOAD_TOO_LARGE",
    415: "UNSUPPORTED_MEDIA_TYPE",
    422: "VALIDATION_FAILED",
    428: "PRECONDITION_REQUIRED",
    429: "TOO_MANY_REQUESTS",
    500: "INTERNAL_ERROR",
    503: "SERVICE_UNAVAILABLE",
}

TYPES: Mapping[int, str] = {
    428: "https://www.rfc-editor.org/rfc/rfc6585#section-3",
    429: "https://www.rfc-editor.org/rfc/rfc6585#section-4",
}


class ProblemResponse(BaseModel):
    """OpenAPI schema of every error body."""

    type: str
    title: str
    status: int
    detail: str
    code: str
    trace_id: str | None = Field(default=None, alias="traceId")
    errors: dict[str, list[str]] | None = None
    current_version: int | None = Field(default=None, alias="currentVersion")


class ProblemError(Exception):
    """An HTTP-level failure (bad header, auth, limits). Business failures use DomainError instead."""

    def __init__(
        self,
        status: int,
        detail: str,
        *,
        code: str | None = None,
        headers: Mapping[str, str] | None = None,
        extra: Mapping[str, Any] | None = None,
    ) -> None:
        super().__init__(detail)
        self.status = status
        self.detail = detail
        self.code = code or CODES.get(status, "ERROR")
        self.headers = dict(headers or {})
        self.extra = dict(extra or {})


def problem(
    status: int,
    detail: str,
    *,
    code: str | None = None,
    headers: Mapping[str, str] | None = None,
    extra: Mapping[str, Any] | None = None,
) -> JSONResponse:
    body: dict[str, Any] = {
        "type": TYPES.get(status, "about:blank"),
        "title": HTTPStatus(status).phrase,
        "status": status,
        "detail": detail,
        "code": code or CODES.get(status, "ERROR"),
        **(extra or {}),
    }
    span = trace.get_current_span().get_span_context()
    if span.is_valid:
        body["traceId"] = format(span.trace_id, "032x")
    return JSONResponse(body, status_code=status, headers=dict(headers or {}), media_type=PROBLEM_JSON)


def from_error(error: ProblemError) -> JSONResponse:
    return problem(error.status, error.detail, code=error.code, headers=error.headers, extra=error.extra)
