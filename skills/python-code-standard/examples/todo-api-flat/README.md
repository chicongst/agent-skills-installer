# taskboard — flat-layout reference (in-memory)

The flat counterpart of `../todo-api`: same HTTP contract and safety rules, one package per feature with seven modules. Written by an agent following the skill, then reviewed by the council and fixed. 130 tests, 98 % branch coverage.

FastAPI + Pydantic v2, PyJWT, structlog + OpenTelemetry, uv, ruff, mypy strict, import-linter, pytest. Storage is in memory behind a `TodoRepository` port; **PostgreSQL is not implemented or tested yet** (see "Adding a database").

**Layout: flat** (`taskboard/todos/{domain,ports,service,repository,schemas,dependencies,router}.py`) — of the layered-layout triggers none holds today: one storage backend (in-memory, and "swap to a DB later" does not count), one entry point (the API), invariants on one entity, a small team.

## Run

```bash
uv sync
uv run ruff format --check . && uv run ruff check .
uv run mypy .
uv run lint-imports
uv run pytest                    # branch coverage ≥ 90 %

# Development: in-memory storage + a locally signed token
cp .env.example .env
uv run python scripts/dev_token.py user-alex      # creates .dev/ keys once, prints a bearer token
uv run --env-file .env uvicorn taskboard.main:create_app --factory --reload
```

Settings come from real environment variables only (`TASKBOARD_` prefix, nested with `__`). `TASKBOARD_STORAGE__DRIVER` and `TASKBOARD_AUTH__*` have no defaults, and `TASKBOARD_ENVIRONMENT` defaults to `production`, which refuses to start because no durable backend exists yet; run with `TASKBOARD_ENVIRONMENT=development` (see `.env.example`). That is intended.

## Folder structure

```
pyproject.toml  uv.lock  .python-version   # deps, ruff, mypy, pytest, import-linter contracts
.env.example                               # the only committed env file
scripts/dev_token.py                       # local RS256 key pair + token
docs/decisions/                            # ADR-001..004
src/taskboard/
├── main.py            # create_app(): settings → logging/telemetry → container → middleware → routers
├── settings.py        # pydantic-settings, validated at boot
├── container.py       # process singletons: clock, repository; readiness checks
├── shared/            # pure: DomainError/ErrorKind, Clock, Patch/UNSET, Page, owner id limit
├── web/               # problem+json, exception handlers, strict JSON route, ETag/If-Match, auth,
│                      #   rate limit, body limit, request log, health
├── infrastructure/    # structlog + OpenTelemetry
└── todos/
    ├── domain.py        # TodoItem (frozen dataclass + rules), enums, domain errors
    ├── ports.py         # TodoRepository Protocol, TodoListQuery, WriteResult = Written | Missing | Stale
    ├── service.py       # TodoService: every use case; version-checked writes
    ├── repository.py    # InMemoryTodoRepository (asyncio.Lock, version-guarded writes)
    ├── schemas.py       # request/response/query models
    ├── dependencies.py  # TodoServices Protocol → TodoService per request
    └── router.py        # /v1/todos
tests/
├── conftest.py  fakes.py   # signing key, settings factory, Api client fixture; FixedClock, RacingTodoRepository
├── unit/                   # domain, service, architecture, settings
└── integration/            # HTTP contract (parametrised per backend), limits, request log
```

## Dependency rule

```
router → dependencies → schemas | service → ports → domain → shared
repository → ports, domain          (only container.py imports it)
main / container → everything        (composition root)
```

| Module | Must never import | Enforced by |
|---|---|---|
| `todos.domain`, `todos.ports`, `todos.service`, `shared` | FastAPI, Starlette, Pydantic, JWT, OTel, `web`, `infrastructure`, `settings`, `container` | import-linter |
| `todos.service` | `todos.repository` | import-linter |
| `todos.router`, `todos.dependencies`, `todos.schemas` | `container`, `main`, `todos.repository` | import-linter (`TodoServices` Protocol instead) |
| `web`, `infrastructure` | `todos` | import-linter |

## How instances are created

| Object | Lifetime | Created in |
|---|---|---|
| `Settings` | process | `create_app` |
| Tracer / meter providers | process (first call wins) | `configure_telemetry` |
| `Container` (clock, repository) | app | `build_container` |
| `TokenVerifier`, `WriteRateLimiter` | app | `create_app` → `app.state` |
| `TodoService` | request | `todos/dependencies.py` |

## HTTP contract (`/v1/todos`)

| Method + path | Purpose | Success |
|---|---|---|
| `POST /v1/todos` | create `{title, description?, dueDate?, priority?: low/medium/high}` | 201 + `Location` + `ETag` |
| `GET /v1/todos` | `?status=open\|done&q=&sort=createdAt\|-createdAt\|dueDate\|-dueDate&limit=1..100&offset=0..10000` | 200 `{items,total,limit,offset}` |
| `GET /v1/todos/{id}` | one todo | 200 + `ETag` |
| `PATCH /v1/todos/{id}` | partial update; absent = keep, `null` = clear (`title: null` → 422) | 200 + `ETag` |
| `POST /v1/todos/{id}/complete` · `/reopen` | mark done / reopen | 200 + `ETag` |
| `DELETE /v1/todos/{id}` | delete | 204 |

All writes except create require `If-Match: "<version>"` (exactly one strong ETag).

| Situation | Status | `code` |
|---|---|---|
| No, invalid, expired, wrong-issuer or wrong-audience token | 401 + `WWW-Authenticate` | `UNAUTHORIZED` |
| Valid token whose `sub` is missing, blank, padded, > 128 chars or contains NUL | 403 | `FORBIDDEN` |
| Write without `Authorization` (checked before the body is read) | 401 | `UNAUTHORIZED` |
| Malformed JSON (incl. BOM, lone surrogate, deep nesting) / duplicate key | 400 | `MALFORMED_JSON` / `DUPLICATE_KEY` |
| Body not `application/json` | 415 | `UNSUPPORTED_MEDIA_TYPE` |
| Unknown field, wrong type, bad date/enum, bad query, bad UUID, domain rule, empty PATCH | 422 | `VALIDATION_FAILED` + `errors{camelCaseField}` |
| Unknown todo or another user's todo | 404 | `TODO_NOT_FOUND` |
| Unknown route / method | 404 / 405 | `NOT_FOUND` / `METHOD_NOT_ALLOWED` |
| Write without `If-Match` or with `*` | 428 | `PRECONDITION_REQUIRED` |
| Malformed `If-Match` (incl. a list) | 400 | `INVALID_IF_MATCH` |
| Weak or stale ETag | 412 (+ `currentVersion` when stale) | `VERSION_MISMATCH` |
| Body over `TASKBOARD_MAX_BODY_BYTES` (1 MiB) | 413 | `PAYLOAD_TOO_LARGE` |
| Over `TASKBOARD_WRITE_RATE_LIMIT` (60/minute) per user, per replica | 429 + `Retry-After` | `TOO_MANY_REQUESTS` |
| Unhandled exception | 500 | `INTERNAL_ERROR` (no exception text) |

A PATCH whose values equal the current ones, completing a done todo or reopening an open one returns 200 with the same version and writes nothing. Search is a case-insensitive substring match on the title with `%`, `_`, `\` taken literally; due-date sorting puts todos without a due date last in both directions; ties are broken by id.

## Where does new code go?

| You are adding… | Put it in |
|---|---|
| A business rule | `todos/domain.py` + a test in `tests/unit/todos/test_domain.py` |
| A new action | a method on `TodoService`, a route in `todos/router.py`, contract tests |
| A database | see below |
| A config value | a field on `Settings`; no default if a wrong default is unsafe |
| A second resource or entry point | reconsider the layered layout (skill rule 2) |
| A decision someone will question later | `docs/decisions/ADR-00N-<title>.md` |

## Adding a database

1. `todos/sql_repository.py` implementing `TodoRepository` with `UPDATE … WHERE id, owner_id, version = :expected RETURNING version` and the semantics in the `TodoRepository` docstring.
2. `PostgresStorage` settings variant → `storage: MemoryStorage | PostgresStorage` discriminated on `driver`; a branch in `build_container`; a database readiness check.
3. Alembic migrations as a deploy step, a `"postgres"` param on the `api` fixture (Testcontainers), a column ↔ dataclass test, driver instrumentation.
