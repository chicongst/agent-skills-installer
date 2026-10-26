# ADR-004: Strict JSON request bodies

**Status:** accepted

## Context
FastAPI 0.162 parses the body with `json.loads` and validates the resulting dict in Pydantic's lax Python mode (verified):
- `{"dueDate": 0}` becomes 1970-01-01; `"yes"` becomes `True`; `{"title":"a","title":"b"}` silently keeps `"b"`.
- `ConfigDict(strict=True)` on the model rejects every valid ISO date and enum string, because strict Python mode wants `date` / enum instances.

## Decision
`web.strict_json.StrictJsonRoute` (the documented custom `APIRoute` hook) validates the raw bytes first: `Content-Type` must be `application/json` (415), duplicate keys are rejected (400 `DUPLICATE_KEY`), and the body model is validated with `model_validate_json(raw, strict=True)` (422 with field paths). Endpoints keep a normal `body: CreateTodoRequest` parameter, so OpenAPI is unchanged. Request models extend `InputModel` (`extra="forbid"`, frozen) with camelCase aliases. The strict pass is an addition, not a replacement: with an alias generator, strict `model_validate_json` silently ignores a snake_case key, and it is FastAPI's own validation afterwards that rejects it as an unknown field (422).
- PostgreSQL text cannot store NUL (`\u0000`); the domain rejects it in every string so both backends answer 422 instead of the database raising a 500.

## Consequences
- The body is parsed twice (once to find duplicate keys); negligible next to I/O.
- FastAPI reads the body before dependencies run, so `strict_handler` refuses a request without `Authorization` (401) before parsing; otherwise anonymous callers could learn the schema from 422s even though OpenAPI is off in production. `CurrentOwner` still verifies the token.
- Bytes that `json.loads` accepts but Pydantic's parser rejects (BOM, lone surrogate, nesting > 200) are 400 `MALFORMED_JSON`, not 422.
- Strings reject Unicode control/format characters (`Cc`/`Cf`, except `\n`/`\t` in the description).
- Query strings stay lax (they are strings by nature) but use a `ListTodosParams` model with `extra="forbid"`, `Literal` sorts and bounded ints.
