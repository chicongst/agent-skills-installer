# todo-api — reference Python 3.14 service structure

**Layout:** layered on purpose, as the worked example of the skill's 2+ layout (rule 2). A real service this size — one production backend, one entry point, one entity — would use the flat layout (`../todo-api-flat`). 

FastAPI + Pydantic v2, SQLAlchemy 2.1 async (asyncpg) + Alembic, PyJWT, structlog + OpenTelemetry, uv, ruff, mypy strict, import-linter, pytest + Testcontainers. 205 tests, 99 % branch coverage; the HTTP contract runs on the in-memory and the PostgreSQL backend.

## Run

```bash
uv sync                                   # creates .venv from uv.lock
uv run ruff format --check . && uv run ruff check .
uv run mypy .                             # strict
uv run lint-imports                       # layer contracts
uv run pytest                             # needs Docker (PostgreSQL via Testcontainers); branch coverage ≥ 90 %

# Development: in-memory storage + a locally signed token
cp .env.example .env
uv run python scripts/dev_token.py user-alex      # creates .dev/ keys once, prints a bearer token
uv run --env-file .env uvicorn todo_api.main:create_app --factory --reload

# PostgreSQL locally
export TODO_DB_PASSWORD=change-me
docker compose up -d postgres
export TODO_ENVIRONMENT=development TODO_STORAGE__DRIVER=postgres
export TODO_STORAGE__DATABASE_URL="postgresql+asyncpg://todo:$TODO_DB_PASSWORD@localhost:5432/todo"
uv run alembic upgrade head
uv run --env-file .env uvicorn todo_api.main:create_app --factory

# Schema change
uv run alembic revision --autogenerate -m "add tags"   # review the file, then
uv run alembic check                                     # CI: models and migrations agree
```

Production runs `alembic upgrade head` as a separate deploy step (a job or init container using the same image), never at app start; `migrations/env.py` sets `lock_timeout = 5s` so a migration fails fast instead of queueing behind live traffic. The first migration runs `CREATE EXTENSION IF NOT EXISTS pg_trgm`; on managed PostgreSQL the migration role needs permission for that (RDS: `rds_superuser`), otherwise a DBA creates the extension once beforehand.

Settings come from real environment variables only. `TODO_STORAGE__DRIVER` and `TODO_AUTH__*` have no defaults, and `TODO_ENVIRONMENT` defaults to `production`, which refuses `memory` storage and open docs. A missing or unsafe value stops `create_app` before the server binds (verified with `uvicorn … --factory` and the Docker image).

## Folder structure

```
pyproject.toml                 # deps, ruff, mypy, pytest, import-linter contracts
uv.lock  .python-version       # pinned resolution and interpreter
alembic.ini  migrations/       # async env.py, date-named revisions
compose.yaml  Dockerfile       # local PostgreSQL; non-root image built from uv.lock
.env.example                   # the only committed env file
scripts/dev_token.py           # local RS256 key pair + token
docs/decisions/                # ADR-001..007: why it looks like this
src/todo_api/
├── main.py                    # create_app(): settings → logging → container → middleware → routers
├── settings.py                # pydantic-settings, TODO_ prefix, nested with __, validated at boot
├── container.py               # process singletons: clock, repository, engine; readiness checks
├── shared/                    # pure: DomainError/ErrorKind, Clock, Patch/UNSET, Page, owner id limit
├── web/                       # HTTP cross-cutting: problems (+ OpenAPI schema), exception handlers, strict JSON,
│                              #   ETag/If-Match, auth (CurrentOwner), rate limit, body limit, request log, health
├── infrastructure/            # SQLAlchemy Base/engine, structlog + OpenTelemetry (traces, metrics, asyncpg)
└── todos/                     # one feature
    ├── domain/                # TodoItem (frozen dataclass + rules), enums, errors — no framework imports
    ├── application/
    │   ├── ports.py           # TodoRepository Protocol, TodoListQuery, WriteResult = Written | Missing | Stale
    │   ├── use_cases/         # one module per use case: <Action>Command + <Action>Handler.handle()
    │   ├── versioned_write.py # load → check version → pure change → guarded write
    │   └── audit_log.py       # business log lines (not domain events; see the skill's outbox rule)
    ├── infrastructure/        # tables.py (mapping), sql_repository.py, in_memory_repository.py
    └── http/                  # router.py, schemas.py (request/response models), dependencies.py
tests/
├── conftest.py  fakes.py      # signing key + settings factory; FixedClock, RacingTodoRepository (the real
│                              #   in-memory adapter plus a lose-the-race hook — no second fake)
├── unit/                      # domain rules, handlers, architecture, settings
└── integration/               # HTTP contract on memory AND PostgreSQL, repository races, limits, health, telemetry
```

## Dependency rule

```
todos.http ───────────┐
                      ├─▶ todos.application ─▶ todos.domain ─▶ shared
todos.infrastructure ─┘
main / container ─▶ everything (composition root)
```

| Package | May import | Must never import | Enforced by |
|---|---|---|---|
| `todos.domain`, `shared` | stdlib, `shared` | FastAPI, Pydantic, SQLAlchemy, JWT, OTel, `web`, `infrastructure` | import-linter |
| `todos.application` | `domain`, `shared` | same as above | import-linter |
| `todos.infrastructure` | `application`, `domain`, SQLAlchemy | `todos.http` | import-linter |
| `todos.http` | `application`, `domain`, `web`, FastAPI, Pydantic | `todos.infrastructure`, `container` | import-linter (`TodoServices` Protocol instead) |
| `web`, `infrastructure` | `shared`, frameworks | any feature | import-linter |

## How instances are created

| Object | Lifetime | Created in | Why |
|---|---|---|---|
| `Settings` | process | `create_app` | read once, fail fast |
| Tracer and meter providers, asyncpg instrumentation | process | `configure_telemetry` (first call wins) | OTel globals can be set once per process |
| `Container` (clock, repository, engine) | process | `build_container` | the engine pool and in-memory state must be shared |
| `TokenVerifier`, `WriteRateLimiter` | process | `create_app` → `app.state` | JWKS cache, limiter window |
| Handlers | request | `todos/http/dependencies.py` | cheap; take the repository + clock |
| SQLAlchemy session | repository call | `SqlTodoRepository` | one short transaction (ADR-006) |

No module-level app, engine or settings: tests build a fresh app per test with `create_app(make_settings(...))` and a unique owner id, so they never share data even on one PostgreSQL container.

## HTTP contract (`/v1/todos`)

| Situation | Status | `code` |
|---|---|---|
| No, invalid, expired, wrong-issuer or wrong-audience token | 401 + `WWW-Authenticate` | `UNAUTHORIZED` |
| Valid token whose `sub` is missing, blank, padded, over 128 chars or contains NUL | 403 | `FORBIDDEN` |
| Write without `Authorization` (checked before the body is read) | 401 | `UNAUTHORIZED` |
| Malformed JSON (incl. BOM, lone surrogate, nesting > 200) | 400 | `MALFORMED_JSON` |
| Duplicate key in the body | 400 | `DUPLICATE_KEY` |
| Body not `application/json` | 415 | `UNSUPPORTED_MEDIA_TYPE` |
| Unknown field (incl. snake_case keys), wrong type, `0` as date, impossible date, miscased/comma enum, bad query, bad UUID | 422 | `VALIDATION_FAILED` + `errors` |
| Domain rule (blank or long title, control/invisible characters, `title: null`) / empty PATCH | 422 | `VALIDATION_FAILED` + `errors.<camelCaseField>` / `errors.body` |
| Unknown todo or another user's todo | 404 | `TODO_NOT_FOUND` |
| Unknown route / method | 404 / 405 | `NOT_FOUND` / `METHOD_NOT_ALLOWED` |
| Write without `If-Match` or with `*` | 428 | `PRECONDITION_REQUIRED` |
| Malformed `If-Match`, including a list (`"1", "2"`): one strong ETag only | 400 | `INVALID_IF_MATCH` |
| Weak or stale ETag | 412 (+ `currentVersion` when stale) | `VERSION_MISMATCH` |
| Body over `TODO_MAX_BODY_BYTES` (1 MiB) | 413 | `PAYLOAD_TOO_LARGE` |
| Over `TODO_WRITE_RATE_LIMIT` per user (per replica) | 429 + `Retry-After` | `TOO_MANY_REQUESTS` |
| Database unreachable on `/health/ready` | 503 | `SERVICE_UNAVAILABLE` |
| Unhandled exception | 500 | `INTERNAL_ERROR`, no exception text |

A PATCH whose values equal the current ones, or completing a done todo, returns 200 with the same version and writes nothing. All errors are RFC 9457 `application/problem+json` with `traceId`; `errors` keys use the wire (camelCase) names; an unknown key is reported exactly as sent. Search is case-insensitive via `lower()`/`ILIKE`; a few Unicode letters (`İ`) fold differently in memory and PostgreSQL. Lists: `?status=open|done&q=&sort=createdAt|-createdAt|dueDate|-dueDate&limit=1..100&offset=0..10000`, nulls last in both directions, ties broken by id.

## Request flow — `PATCH /v1/todos/{id}`

1. `RequestLogMiddleware` times the request (one `http.request` log line with the route template); `BodyLimitMiddleware` caps the body; `StrictJsonRoute` checks the content type, duplicate keys and strict JSON types.
2. Dependencies: `CurrentOwner` verifies the JWT, `limit_writes` counts the write, `expected_version` parses `If-Match`.
3. `UpdateTodoRequest.to_changes()` turns `model_fields_set` into `TodoChanges` (`UNSET` = not sent, `None` = clear).
4. `UpdateTodoHandler` → `versioned_write.save`: load the owner's todo, compare versions, call the pure `TodoItem.apply`, then `repository.update(changed, expected_version)`.
5. `SqlTodoRepository.update`: `UPDATE … WHERE id, owner_id, version = :expected RETURNING version`; a miss returns `Missing()` or `Stale(current)` from the same transaction.
6. Domain errors bubble to `install_exception_handlers`, which maps `ErrorKind` → 422/404/412; conflicts are logged as `todo.version_conflict`.

## Where does new code go?

| You are adding… | Put it in |
|---|---|
| A business rule | `todos/domain/todo.py` (+ error in `errors.py`) and a test in `tests/unit/todos` |
| A new action | `todos/application/use_cases/<action>.py` (command + handler), a factory in `http/dependencies.py`, a route in `http/router.py`, contract tests |
| A new storage backend | `todos/infrastructure/<name>_repository.py`, a branch in `build_container`, a new `api` fixture param |
| A schema change | `todos/infrastructure/tables.py`, then `alembic revision --autogenerate` and `alembic check` |
| A config value | a field on `Settings` (or a nested model) with validation; no default if a wrong default is unsafe |
| A notification to another system after a write | an outbox row written in the same transaction, delivered by a worker — never a call after commit |
| An outbound HTTP call | a port in `application`, an adapter in `infrastructure` using one shared `httpx2.AsyncClient` with timeouts |
| A role or partner scope | a dependency next to `CurrentOwner` in `web/auth.py`, applied to the router |
| A new resource ("projects") | `todo_api/projects/{domain,application,infrastructure,http}` + an import-linter container entry |
| A decision someone will question later | `docs/decisions/ADR-00N-<title>.md` |
