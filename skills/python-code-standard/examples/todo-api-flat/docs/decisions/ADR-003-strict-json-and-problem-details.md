# ADR-003: Strict JSON bodies and problem+json errors

**Status:** accepted

## Decision
- `web.strict_json.StrictJsonRoute` checks `Content-Type` (415), rejects duplicate keys (400 `DUPLICATE_KEY`) and validates the raw body with `model_validate_json(strict=True)` before FastAPI's own (lax) validation, so `0` is not a date and `1` is not a priority. FastAPI's pass still runs and rejects snake_case keys.
- The domain raises `DomainError` subclasses; `web.exception_handlers` is the only place that maps them (and every framework error) to RFC 9457 `application/problem+json` with a stable `code` and `traceId`.
- NUL is rejected in every stored or searched string so a future PostgreSQL backend behaves the same as memory.

## Consequences
The body is parsed twice (negligible). The strict check runs before auth, so an anonymous malformed body gets 400/415/422 rather than 401; nothing executes and the schema is public, so this is accepted.
