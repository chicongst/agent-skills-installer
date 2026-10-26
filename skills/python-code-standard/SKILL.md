---
name: python-code-standard
description: Use when writing, scaffolding, or extending Python backend code — FastAPI/Starlette APIs, services, workers, SQLAlchemy/Alembic data access, pyproject/uv/ruff/mypy setup — or when the user asks for production-grade, "chuẩn", large-project-quality Python. Not for reviewing existing code (use `code-review`), restructuring with identical behavior (use `refactor`), throwaway scripts or notebooks, or other languages (use `nodejs-code-standard` / `dotnet-code-standard`).
---

# Python Code Standard

Write Python the way the most-starred Python application repos do: feature packages whose layers import inwards (and a linter that proves it), one use-case boundary per action, domain exceptions mapped once to problem+json, strict JSON at the boundary, authenticated owner-scoped data, settings validated at boot, observable dependencies, and a toolchain where ruff, mypy strict and the tests all pass. **"It runs" is not done. Done = `ruff check`, `ruff format --check`, `mypy .` (strict), `lint-imports` and `pytest --cov` green — against the real database whenever the service has one.**

Project conventions and CLAUDE.md win over this skill. Read 2–3 neighbouring modules before adding code to an existing codebase.

## Sources (stars checked 2026-10-26)

| Repo | ★ | What we take from it |
|---|---|---|
| fastapi/fastapi | 104k | `Annotated` dependencies, lifespan, response models, async tests with `ASGITransport` |
| fastapi/full-stack-fastapi-template | 46k | `requires-python>=3.14`, uv workspace + lockfile, mypy strict, PyJWT + pwdlib, migrations in a prestart step |
| zhanymkanov/fastapi-best-practices | 18k | package per domain, custom base models, async test client from day 0, `dependency_overrides` over monkeypatching |
| pydantic/pydantic · sqlalchemy/sqlalchemy | 29k · 12k | strict JSON-mode validation, `Mapped[]`, async sessions, naming conventions |
| polarsource/polar | 10k | `create_app()` + lifespan, feature modules with `repository.py`, one error base + handler, structlog + OTel, `/healthz` with dependency checks, ownership-scoped queries → 404 |
| astral-sh/ruff · uv · python/mypy | 50k · 91k · 21k | tooling |

Netflix/dispatch is archived and cosmicpython/code is stale (Flask); use them for history only. The reference services `examples/todo-api/` (layered) and `examples/todo-api-flat/` (flat) were scored by a two-role review council over two rounds (principal architect + quality/security reviewer); its findings are folded into the rules below.

## Rules (non-negotiable)

**Project & structure** — tree, lifetimes and HTTP contract: `examples/todo-api/README.md`
1. `src/` layout, `pyproject.toml` (PEP 621 + `[dependency-groups] dev`), committed `uv.lock`, `.python-version`, `requires-python` pinned to the minor you test on. Everything runs through `uv run`; CI uses `uv sync --locked`. `compose.yaml` for local dependencies (skip it when there are none), a non-root `Dockerfile` built from `uv.lock` for anything that will be deployed, `docs/decisions/` for ADRs, `.env.example` is the only committed env file. `tests/__init__.py` + `--import-mode=importlib` so tests import shared helpers as `tests.conftest`. When the task allows in-memory storage, follow patterns §11.
2. Pick the layout from what is true **today** and say which and why in one README line. Count only: more than one *production* storage backend (an in-memory dev/test adapter and "swap to a DB later" do not count), more than one real entry point (API + worker/CLI), invariants spanning several entities, a team larger than two (only when the user or CLAUDE.md states it — never guess).
   - **Flat (default; 0–1 hold):** `<app>/<feature>/{domain.py, ports.py, service.py, repository.py, schemas.py, dependencies.py, router.py}`. Domain errors live in `domain.py`; the version-checked write is a private method of the service class.
   - **Layered (2+ hold):** `<app>/<feature>/{domain,application,infrastructure,http}/` as in `examples/todo-api`.
   Both: cross-cutting HTTP code in `<app>/web`, DB/telemetry plumbing in `<app>/infrastructure`, pure helpers in `<app>/shared`.
3. **import-linter contracts in `pyproject.toml`**: a `layers` contract per feature (layered: `http | infrastructure → application → domain`; flat: `router → dependencies → schemas | service | repository → ports → domain`, plus `forbidden` contracts so `router`, `schemas` and `service` never import `repository` — only the container does — and `repository` never imports FastAPI, Pydantic or `router`), and a `forbidden` contract keeping domain, ports, use cases/service and `shared` free of FastAPI, Pydantic, SQLAlchemy, JWT and OpenTelemetry. `web`/`infrastructure` never import a feature. HTTP code reaches the composition root through a `Protocol`, not by importing `container.py` (that would import infrastructure transitively). Prove a contract bites by adding a bad import once.
4. Domain = frozen `slots` dataclasses + `StrEnum`s + rules; `create(...)` classmethod validates, behaviour methods return a **new** instance via `dataclasses.replace` with `version + 1` — or `self` when nothing changed. No framework imports, no I/O, time passed in. Error `field`s and `details` keys use attribute names (`due_date`, `current_version`); the web layer converts them to wire names. Don't re-check what the type system and the boundary already guarantee.
5. Use cases: layered → one module per use case (frozen `<Action>Command` + `<Action>Handler.handle(command)`, ADR-007); flat → one `service.py` with one class per aggregate (Polar's style). Never mix both in one feature. Ports are `typing.Protocol`s. Write outcomes are a tagged union (`Written | Missing | Stale(current_version)`) matched with `match` + `assert_never`.
6. Infrastructure implements ports. **One** in-memory adapter serves development and unit tests and matches the SQL adapter's semantics (`lower()` like `ILIKE`, nulls last, NUL rejected upstream); test-only behaviour (losing a race) is a small subclass in `tests/fakes.py`, never a second fake that silently ignores filters. Plus `FixedClock`.
7. `main.py:create_app(settings=None)` is the composition root — no module-level `app`, engine, session or settings. Run with `uvicorn <app>.main:create_app --factory`. `container.py` builds process singletons (engine, repositories, clock); handlers are built per request by `Annotated[Handler, Depends(factory)]` aliases in `<feature>/http/dependencies.py`. Lifespan disposes the engine.

**Security**
8. Authentication on every feature route through one `CurrentOwner = Annotated[str, Depends(current_owner)]`: PyJWT with an explicit algorithm list, required `exp`/`iss`/`aud`, keys from JWKS (`PyJWKClient`, fetched via `asyncio.to_thread`) or a public-key file in development. No/invalid token → 401 + `WWW-Authenticate: Bearer`; valid token without `sub` → 403. A unit test walks the router's dependants and fails if any feature route lacks `current_owner`. `sub` must be non-blank, unpadded, NUL-free and fit the owner column, else 403 — so one person never maps to two owners. Ownership lives in the aggregate and every repository query; another owner's resource is **404**. The settings type allows only asymmetric algorithms (`Literal["RS256","PS256","ES256","EdDSA"]`).
9. Writes are rate limited per user (`limits` moving window) → 429 problem with `type` and `Retry-After`; in-memory storage makes it per replica — say so in an ADR. Creates called by retrying clients (partners, queue consumers, offline sync) accept an `Idempotency-Key` (patterns §13); for a first-party UI record the skip in an ADR. URL-version (`/v1`) before exposing to partners.

**Errors**
10. Expected failures raise `DomainError` subclasses (`kind`, `code`, `message`, `field`, `details`) — never `HTTPException` from domain/application. HTTP-only failures raise `web.problems.ProblemError`. Python has no Result-type convention; don't invent one.
11. One `install_exception_handlers(app)` renders **every** error as RFC 9457 `application/problem+json` with a stable `code` and `traceId`: domain errors by kind, `RequestValidationError` and strict-body errors as 422 `errors{field: [msg]}`, Starlette `HTTPException` (404/405) by status, `Exception` → 500 logged with stack, no exception text. 400 only for unparseable JSON (`MALFORMED_JSON`), duplicate keys (`DUPLICATE_KEY`) and malformed headers. `errors` keys use the wire names (camelCase) for body, query and path alike.
12. `ErrorKind` lists only kinds something raises; the web layer maps kind → status in one dict.

**Input/output**
13. **Request bodies are validated in strict JSON mode** (patterns §1): FastAPI validates in lax Python mode — `0` becomes a date, `"yes"` a bool, duplicate keys silently win — and model-wide `strict=True` rejects every valid ISO date and enum. Use a `StrictJsonRoute` (`APIRoute` subclass, `route_class=`) that checks `Content-Type` (415), rejects duplicate keys (400) and runs `model_validate_json(raw, strict=True)` — as an **extra** pass: FastAPI's own validation still runs and is what rejects snake_case keys on alias models. Bytes that Python's `json` accepts but Pydantic's parser rejects (BOM, lone surrogates, deep nesting) are 400 `MALFORMED_JSON` too. Reject control and invisible format characters (Unicode `Cc`/`Cf`; allow `\n`/`\t` in multi-line fields) in every stored string and `\u0000` in every searched one — PostgreSQL cannot store NUL (→ 500), ESC injects terminal sequences, zero-width spaces make text look blank. Because FastAPI reads the body before dependencies, the strict route refuses a request without `Authorization` (401) before parsing it; the dependency still verifies the token. Request models extend an `InputModel` with `extra="forbid"`, frozen, camelCase aliases. Responses are separate `OutputModel`s with a `from_domain` classmethod; never return ORM rows or domain objects.
14. PATCH distinguishes absent from null via `model_fields_set` → a domain `TodoChanges` whose fields default to an `UNSET` sentinel (`type Patch[T] = T | Literal[Unset.UNSET]`). Query strings go through a Pydantic params model (`Annotated[Params, Query()]`, `extra="forbid"`, `Literal` sorts, **every** int bounded on both sides — `limit` 1..100, `offset` 0..10 000 — because an unbounded offset overflows the driver's int64 → 500 on PostgreSQL only).
15. Lists are bounded (default 20, max 100), deterministic (tie-break on id), nulls last in both directions. Offset + `total` for small per-user lists; keyset for large or partner-facing ones. Substring search on Postgres gets a `pg_trgm` GIN index; escape `%`, `_` and `\` in `LIKE`. Body size is capped by an ASGI middleware (uvicorn has no limit) → 413.

**Data**
16. SQLAlchemy 2.x typed `Mapped[]` with a `MetaData(naming_convention=...)`, `DateTime(timezone=True)`, `Enum(..., native_enum=False, create_constraint=True, values_callable=...)`, explicit lengths and indexes from the queries you run. Async engine (asyncpg) with pool, connect and command timeouts, `async_sessionmaker(expire_on_commit=False)`.
17. Full-entity writes use one mapping function that reads **every mapped column** from the aggregate (`{c: getattr(todo, c) for c in COLUMNS}`) plus a test asserting columns == dataclass fields — a hand-written column list silently drops new columns. Guard with `UPDATE … WHERE id, owner_id, version = :expected RETURNING version`; on a miss, one `SELECT version` in the same transaction returns `Missing` or `Stale(current)`.
18. Alembic with an async `env.py`, date-named revisions, the URL from an environment variable (never in `alembic.ini`), `alembic check` in CI. Migrations run as a deploy step (job / init container), never at app start, never `metadata.create_all`. Zero-downtime by default (patterns §14): `SET LOCAL lock_timeout` inside the migration transaction, expand → backfill in batches → contract across releases, `CREATE INDEX CONCURRENTLY` in `autocommit_block()` on live tables, and extensions treated as an ops prerequisite on managed PostgreSQL.
19. Shared mutable resources use optimistic concurrency: `version` + `ETag` + required `If-Match` (missing or `*` → 428, weak → 412, malformed → 400, stale → 412 with `currentVersion`). A no-op — including a PATCH whose values equal the current ones — returns the current state without writing or bumping the version. Accept exactly one strong ETag in `If-Match` and document it.
20. Transactions: one short `async with sessions.begin()` per repository call when each use case writes one aggregate; a `UnitOfWork` port when it writes several. Never `await` two queries on one `AsyncSession` concurrently. Parameterised queries only. A write that must notify another system writes an **outbox** row in the same transaction, delivered by a worker — never a call after commit.

**Async**
21. `async def` end to end on the request path; no blocking calls (`requests`, `time.sleep`, sync file/DNS/JWKS fetches) on the event loop — `asyncio.to_thread` or an async client. Every outbound call has a timeout (`asyncio.timeout`, client timeouts, DB `command_timeout`). One shared `httpx2.AsyncClient` per process for outbound HTTP.

**Config, time, logging, operations**
22. One `pydantic-settings` `Settings` (`env_prefix`, `env_nested_delimiter="__"`, `extra="forbid"`, frozen, **`env_file=None`** — development uses `uv run --env-file .env`, so a stray `.env` on a server changes nothing), loaded once in `create_app`. **No default may select a non-durable or insecure behaviour**: storage and auth have no defaults; safe-direction defaults (`docs_enabled=False`) are fine; `environment` defaults to `production`, whose validator refuses in-memory storage and open docs. Storage variants are discriminated unions (`MemoryStorage | PostgresStorage`) so the type guarantees e.g. the URL; pool sizes and timeouts are settings. An in-memory-only service has a single variant, so its validator is simply `if self.environment == "production": raise ValueError("No durable storage backend exists yet.")` — no one-member union, no always-empty allow-list — and it runs only with `<PREFIX>_ENVIRONMENT=development|test`; say so in the README. Secrets as `SecretStr`.
23. Inject a `Clock` protocol; ban `datetime.now/utcnow/date.today` with ruff `TID251` everywhere except `SystemClock`. IDs from `uuid.uuid7()` (3.14 stdlib).
24. Application code logs with stdlib `logging.getLogger(__name__).info("noun.verb", extra={...})` — stable ids, no tokens or PII; structlog renders every record (uvicorn's too) as JSON with `trace_id`. Lifespan shutdown flushes both the meter and the tracer provider. One `http.request` line per request from an ASGI middleware (method, route template — `<unmatched>` when none, **never the raw path**, which carries attacker-controlled newlines and escapes — status, `duration_ms`). OpenTelemetry: register the tracer **and** meter providers globally once per process (first call wins), exporters only when `OTEL_EXPORTER_OTLP_ENDPOINT` is set; instrument FastAPI per app (uninstrument in lifespan) and the **driver** (`AsyncPGInstrumentor`) — `opentelemetry-instrumentation-sqlalchemy` 0.66b1 silently does nothing on SQLAlchemy 2.1. Test that a SQL span exists. `/health/live` (no checks) and `/health/ready` (dependency checks run concurrently under one configurable timeout below the probe timeout, ~0.8 s → 503 naming every failing check; ok with no checks when there are no dependencies).

**Tooling**
25. ruff with a broad rule set (patterns §10) — do **not** enable `TC` (moving annotations under `TYPE_CHECKING` breaks FastAPI's runtime resolution); mypy `strict = true` + `pydantic.mypy` plugin, `warn_unreachable`; no bare `# type: ignore` (codes required) and none in `src/`. No `noqa` to get green except a commented one-liner.

**Testing**
26. pytest + pytest-asyncio (`asyncio_mode = "auto"`, session loop scope), `--strict-markers`, `filterwarnings = ["error"]`. `tests/unit` (domain, handlers with fakes, architecture, settings) and `tests/integration`. The HTTP contract is one test module run against **every** backend via a parametrised `api` fixture (in-memory and PostgreSQL via Testcontainers + the real Alembic migrations). Each test builds its own app with `create_app(make_settings(...))`, enters `app.router.lifespan_context(app)`, uses `httpx2.AsyncClient(transport=ASGITransport(app, raise_app_exceptions=False))` and a unique owner id. Tokens are real RS256 JWTs signed by a session-scoped test key. Mandatory: N concurrent writers with one ETag → exactly one 200; 401/403; cross-owner 404; every status the API can return asserts its `code`; boundary lengths and NUL in body and query on every backend; a no-op PATCH keeps the version; startup fails without required settings or with unsafe production settings. Branch coverage with `pytest-cov` and `fail_under = 90` in `[tool.coverage.report]`. Names `test_<unit>_<condition>_<expected>`.

**Docs**
27. Every non-obvious structural decision gets a short ADR. The README carries run commands, tree, dependency table, lifetimes, HTTP contract and "where does new code go". Docstrings explain *why*, not what the code says.

## Red flags — stop and fix

| You catch yourself… | Do instead |
|---|---|
| `ConfigDict(strict=True)` on a FastAPI body model "for strictness" | `StrictJsonRoute` + `model_validate_json(raw, strict=True)` |
| A default that silently picks in-memory storage or skips auth | Required setting; dev value in `.env` only |
| `app = FastAPI()` / `engine = create_async_engine(...)` at module level | `create_app()` factory + container + lifespan |
| `raise HTTPException(404)` inside a service | `raise TodoNotFoundError(todo_id)`; map once |
| `session.query(...)` / `Column(...)` / `declarative_base()` | SQLAlchemy 2.0 `select()`, `Mapped[]`, `DeclarativeBase` |
| Hand-written `.values(title=..., description=...)` for a full update | `to_values(aggregate)` from the mapped columns + test |
| `datetime.utcnow()` / `datetime.now()` in a handler | Injected `Clock`; `TID251` ban |
| `logger.info(f"created {todo}")` | `logger.info("todo.created", extra={"todo_id": ...})` |
| `requests.get` / sync JWKS fetch inside `async def` | async client or `asyncio.to_thread`, with a timeout |
| API tests only against the in-memory store | Same contract module against PostgreSQL |
| `alembic upgrade head` in the lifespan | Deploy step; `alembic check` in CI |
| `from fastapi.testclient import TestClient` in new async code | `httpx2.AsyncClient` + `ASGITransport` (Starlette now warns about `httpx`) |
| `python-jose`, `passlib`, `freezegun`, `ORJSONResponse` | PyJWT/joserfc, pwdlib[argon2], time-machine, plain response models (patterns §9) |
| Moving imports under `if TYPE_CHECKING:` in FastAPI modules | Keep runtime imports; `TC` stays off |
| `asyncio.run()` inside a test fixture (Alembic env) | Run it in a `ThreadPoolExecutor` thread (patterns §8) |
| `env_file=".env"` in `Settings` | `env_file=None` + `uv run --env-file .env` |
| A second fake repository in tests | The real in-memory adapter + a subclass hook |
| `SQLAlchemyInstrumentor` on SQLAlchemy 2.1 | `AsyncPGInstrumentor` + a test that a SQL span exists |
| `connection.execute("SET ...")` before `context.begin_transaction()` in Alembic | `context.execute("SET LOCAL ...")` inside it — otherwise nothing commits |
| A route checked only by "I remembered `CurrentOwner`" | The architecture test that walks dependants |

## Reference

- Layered reference: `examples/todo-api/` (PostgreSQL + in-memory) — `README.md` first, then `docs/decisions/`.
- Flat reference: `examples/todo-api-flat/` (in-memory, one feature package) — the default layout from rule 2.
- Before/after patterns, verified framework pitfalls and package choices: `references/patterns.md`.

## Done checklist

- [ ] Structure justified (rule 2); import-linter contracts kept; architecture tests pass
- [ ] `CurrentOwner` on every feature route, ownership in every query, rate limit on writes
- [ ] Use cases per rule 5 (layered: command + handler per module; flat: one service class — never both); ports are Protocols; one in-memory adapter shared by dev and tests
- [ ] Strict JSON bodies (types, unknown, duplicate, content type) and problem+json with `code` everywhere
- [ ] Version-guarded writes from mapped columns; bounded deterministic lists; body size limit
- [ ] No insecure/non-durable defaults; settings fail at boot; migrations as a deploy step
- [ ] Injected clock, `uuid7`, request log line, structured logs with trace ids, OTel traces + metrics incl. database, live/ready health
- [ ] Unit + HTTP contract on every backend + race test + 401/403/404/412/428 + startup failure
- [ ] `ruff check`, `ruff format --check`, `mypy .`, `lint-imports`, `pytest --cov` (≥ 90 % branch) — show the output, do not claim it
