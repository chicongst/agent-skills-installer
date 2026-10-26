# ADR-002: Domain exceptions, one mapping to problem+json

**Status:** accepted

## Context
No top Python app uses Result types; Polar raises `PolarError` subclasses and renders them in one handler. FastAPI's default error bodies (`{"detail": ...}`, 422 lists) differ per error source.

## Decision
- The domain raises `DomainError` subclasses carrying `kind`, `code`, `message`, `field`, `details`, never an HTTP status. HTTP-only failures (headers, auth, limits) raise `web.problems.ProblemError`.
- `web/exception_handlers.py` is the only place that turns errors into responses: RFC 9457 `application/problem+json` with `type`, `title`, `status`, `detail`, a stable `code`, `traceId`, and `errors{field: [messages]}` for validation.
- Status codes: malformed JSON or duplicate keys → **400** `MALFORMED_JSON`; well-formed but invalid input (schema or domain rule) → **422** `VALIDATION_FAILED` (FastAPI and Polar convention; RFC 9110 §15.5.21). Unhandled → 500 `INTERNAL_ERROR`, logged with the stack, no exception text in the body.

## Consequences
Handlers read top-down with no `if result.ok` plumbing. A forgotten `raise` cannot be caught by the type checker, so every error path has a contract test asserting its `code`.
