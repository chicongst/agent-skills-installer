# Python patterns — before/after and verified pitfalls

All behaviour below was checked on Python 3.14.7, FastAPI 0.162, Pydantic 2.14, SQLAlchemy 2.1.6, pytest-asyncio 1.4 (2026-10-26). Code is excerpted from `examples/todo-api/`.

## §1 Strict JSON request bodies

What FastAPI does with a plain `body: Model` (lax Python mode after `json.loads`):

| Input | Lax model | `ConfigDict(strict=True)` | `StrictJsonRoute` |
|---|---|---|---|
| `{"dueDate":"2026-03-01"}` | ok | **422** (wants a `date` instance) | ok |
| `{"priority":"high"}` (StrEnum) | ok | **422** | ok |
| `{"dueDate":0}` | **1970-01-01** | 422 | 422 |
| `{"done":"yes"}` / `{"done":1}` | **True** | 422 | 422 |
| `{"title":"a","title":"b"}` | **"b"** | **"b"** | 400 `DUPLICATE_KEY` |
| `{"due_date":"2026-03-01"}` on a camelCase model | 422 (extra) | **ignored** | 422 (FastAPI's pass) |
| `{"title":"a\u0000b"}` | stored; PostgreSQL → **500** | same | 422 (domain rule) |
| `{"title":"\u200b"}` / `"\u001b[31m"` | stored (looks blank / injects ANSI) | same | 422 (domain rule: no `Cc`/`Cf`) |
| BOM-prefixed body, `"a\ud800b"` | 422 "Invalid JSON" | same | 400 `MALFORMED_JSON` |
| `?offset=9223372036854775808` | PostgreSQL → **500** (int64) | same | 422 (`le=10_000`) |
| `{"title":123}` | 422 | 422 | 422 |
| `text/plain` body | 422 | 422 | 415 |

```python
class StrictJsonRoute(APIRoute):
    def get_route_handler(self):
        handler = super().get_route_handler()
        bodies = [p.field_info.annotation for p in self.dependant.body_params]
        model = bodies[0] if len(bodies) == 1 else None
        if not (isinstance(model, type) and issubclass(model, BaseModel)):
            return handler

        async def strict_handler(request: Request) -> Response:
            await validate_strict_json(request, model)   # 415 / 400 / 422 with field paths
            return await handler(request)

        return strict_handler

router = APIRouter(prefix="/v1/todos", route_class=StrictJsonRoute)
```

Endpoints keep `body: CreateTodoRequest`, so OpenAPI is unchanged. FastAPI reads the body before any dependency runs, so `strict_handler` first refuses a request with no `Authorization` header (401) — otherwise an anonymous caller learns the schema from 422s even when OpenAPI is off in production. A `ValidationError` of type `json_invalid` (BOM, lone surrogate, nesting > 200) maps to 400 `MALFORMED_JSON`, not 422. Per-field `StrictStr`/`StrictBool` is the fallback when you cannot change the route class.

## §2 PATCH: absent vs null

```python
class UpdateTodoRequest(CamelInput):
    title: str | None = None
    description: str | None = None

    def to_changes(self) -> TodoChanges:
        sent = self.model_fields_set
        return TodoChanges(
            title=self.title if "title" in sent else UNSET,
            description=self.description if "description" in sent else UNSET,
        )

class Unset(Enum):
    UNSET = "UNSET"
UNSET: Final = Unset.UNSET
type Patch[T] = T | Literal[Unset.UNSET]      # mypy narrows with `is UNSET`
```

The domain decides what `None` means per field (`title: null` → 422, `description: null` → clear). `{}` → 422 `errors.body`.

## §3 Optimistic concurrency

```python
COLUMNS = tuple(c.key for c in TodoRow.__table__.columns)

def to_values(todo: TodoItem) -> dict[str, object]:
    return {column: getattr(todo, column) for column in COLUMNS}

async def update(self, todo: TodoItem, expected_version: int) -> WriteResult:
    async with self._sessions.begin() as session:
        written = await session.scalar(
            update(TodoRow)
            .where(TodoRow.id == todo.id, TodoRow.owner_id == todo.owner_id, TodoRow.version == expected_version)
            .values(to_values(todo))
            .returning(TodoRow.version)
        )
        return Written() if written is not None else await _miss(session, todo.owner_id, todo.id)
```

`tests/unit/test_architecture.py` asserts `set(COLUMNS) == {f.name for f in fields(TodoItem)}`. SQLAlchemy's `version_id_col` only checks the version the ORM loaded, not the one the client sent in `If-Match`; use the explicit `WHERE`. In-memory: same check under `asyncio.Lock`.

## §4 Settings without unsafe defaults

```python
class MemoryStorage(BaseModel):
    driver: Literal["memory"]

class PostgresStorage(BaseModel):
    driver: Literal["postgres"]
    database_url: SecretStr                          # required by the type, not by an if
    pool_size: int = Field(default=10, ge=1)

type StorageSettings = Annotated[MemoryStorage | PostgresStorage, Field(discriminator="driver")]

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="TODO_", env_nested_delimiter="__", env_file=None,
                                      extra="forbid", frozen=True)
    environment: Literal["development", "test", "production"] = "production"   # the strict value is the default
    storage: StorageSettings
    auth: AuthSettings
    docs_enabled: bool = False

    @model_validator(mode="after")
    def _production_is_durable_and_closed(self) -> Self: ...   # memory storage / open docs → error
```

`create_app()` calls `Settings()` first, so uvicorn prints a traceback naming the missing fields and exits non-zero (it is a traceback, not a friendly message — that is fine for a process supervisor). Development: `uv run --env-file .env uvicorn ...`. Tests construct `Settings(environment="test", storage=MemoryStorage(...), ...)` directly.

## §5 Errors → problem+json

```python
_STATUS_BY_KIND = {ErrorKind.VALIDATION: 422, ErrorKind.NOT_FOUND: 404, ErrorKind.VERSION_MISMATCH: 412}

def install_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(DomainError)            # decorator form keeps handler types narrow for mypy
    async def domain_error(_: Request, error: DomainError) -> JSONResponse: ...
    @app.exception_handler(RequestValidationError) ...   # query/path → 422 errors{field}
    @app.exception_handler(HTTPException) ...            # Starlette 404/405 → NOT_FOUND / METHOD_NOT_ALLOWED
    @app.exception_handler(Exception) ...                # 500, logged with stack, generic detail
```

`app.add_exception_handler(DomainError, fn)` with `fn(request, error: DomainError)` fails mypy (handler type is `Callable[[Request, Exception], …]`); the decorator does not.

## §6 Auth and ownership

```python
claims = jwt.decode(token, key, algorithms=["RS256"], audience=aud, issuer=iss, leeway=30,
                    options={"require": ["exp", "iss", "aud"]})
key = (await asyncio.to_thread(jwks.get_signing_key_from_jwt, token)).key   # PyJWKClient is sync

CurrentOwner = Annotated[str, Depends(current_owner)]   # 401 / 403 / subject
```

Test it with real tokens: a session fixture generates an RSA key, writes the public PEM to a temp file, and settings point `public_key_file` at it. Test wrong `aud`, wrong `iss`, expired, missing `sub`.

## §7 FastAPI / Starlette pitfalls (0.16x)

| Pitfall | Fix |
|---|---|
| `app.routes` holds `_IncludedRouter` objects since 0.16x (lazy include), not `APIRoute`s | Inspect the feature's own `router.routes` in architecture tests |
| Router-level `dependencies=[...]` run before endpoint params; body parsing runs before all dependencies | Put auth inside the rate-limit dependency's chain; accept body-before-auth (§1) |
| `httpx.AsyncClient(transport=ASGITransport(app))` does not run lifespan | `async with app.router.lifespan_context(app):` in the fixture |
| `starlette.testclient` warns `Using httpx … deprecated; install httpx2` (Starlette 1.10) | Tests use `httpx2.AsyncClient` + `httpx2.ASGITransport` |
| `ASGITransport` re-raises app exceptions, so a 500 test crashes | `raise_app_exceptions=False` |
| Strict Content-Type is default since 0.132 → 422 for `text/plain` | `StrictJsonRoute` returns 415 first |
| `ORJSONResponse` deprecated (0.131); responses are serialised by Pydantic | Declare the return type / `response_model` |
| `@app.on_event` | `lifespan=` |
| uvicorn has no body size limit | `BodyLimitMiddleware` (Content-Length + streamed count) |
| uvicorn's loggers print plain text | In `dictConfig`: `uvicorn`, `uvicorn.error`, `uvicorn.access` → `handlers: [], propagate: True`; drop `color_message` |
| `logger.info(..., extra={"event": ...})` under structlog overwrites the message | Use the message as the event name: `logger.info("todo.created", extra=...)` |
| FastAPI ships breaking changes in minor releases | Lockfile; read the release notes before `uv lock --upgrade` |
| `opentelemetry-instrumentation-sqlalchemy` 0.66b1 logs "only instruments sqlalchemy < 2.1" and does nothing | `AsyncPGInstrumentor().instrument()` once per process; assert a SQL span in a test |
| `trace.set_tracer_provider` / `metrics.set_meter_provider` work once per process; tests build many apps | Reuse the provider if one is installed; instrument FastAPI per app and `uninstrument_app` in lifespan |
| Alembic `env.py`: `connection.execute(text("SET ..."))` before `begin_transaction()` autobegins, so the migration never commits (table missing, no error) | `context.execute("SET LOCAL lock_timeout = '5s'")` inside `with context.begin_transaction():` |
| PostgreSQL rejects `\u0000` in text (`CharacterNotInRepertoireError` → 500); memory accepts it | Reject NUL in the domain and in query `pattern`s |
| `to_camel` on an `extra_forbidden` location turns `due_date` into `dueDate`, pointing the client at the valid name | Keep the raw key for `extra_forbidden` errors |
| Repeated query params (`?status=open&status=done`) — the last one silently wins | Accept it, or declare `list[...]` and reject `len > 1`; document which |
| `lower()` (memory) and PostgreSQL `lower()`/`ILIKE` differ on some Unicode (`İ` → `i̇`) | Document the gap, or NFKC-normalise and lower-case into a stored search column |

## §8 Testing patterns

```python
@pytest.fixture(scope="session")
def postgres_url() -> Iterator[str]:
    with PostgresContainer("postgres:17-alpine", driver="asyncpg") as postgres:   # testcontainers.community.postgres
        url = postgres.get_connection_url()
        config = Config(ROOT / "alembic.ini"); config.attributes["url"] = url
        with ThreadPoolExecutor(1) as thread:       # env.py calls asyncio.run; the test loop is already running
            thread.submit(command.upgrade, config, "head").result()
        yield url

@pytest.fixture(params=["memory", pytest.param("postgres", marks=pytest.mark.postgres)])
async def api(request, make_settings, signing_key) -> AsyncIterator[Api]:
    url = request.getfixturevalue("postgres_url") if request.param == "postgres" else None
    async for api in open_api(create_app(make_settings(database_url=url)), signing_key):
        yield api
```

- Isolation = fresh app + `owner=f"user-{uuid4().hex}"`, not truncation.
- Unit tests use the real `InMemoryTodoRepository`; a `RacingTodoRepository(InMemoryTodoRepository)` subclass makes the next update return `Stale(n)` to test the lost-race path.
- Hostile inputs, parametrised on every backend: 200/201-char titles, 5000/5001-char descriptions, NUL in body and `?q=%00`, padded/long/blank `sub`.
- Race test: `asyncio.gather` ten PATCHes with `If-Match: "1"` → exactly one 200, nine 412, final version 2.
- `testcontainers.postgres` is deprecated in 4.15 → import from `testcontainers.community.postgres`.
- Override a dependency to force a 500: `app.dependency_overrides[dependencies._services] = Broken`.

## §9 Packages

| Use | Version (2026-10-26) | Avoid | Why |
|---|---|---|---|
| fastapi | 0.162 | `fastapi-slim` | discontinued |
| pydantic / pydantic-settings | 2.14 / 2.16 | `pydantic.v1` | unsupported on 3.14 |
| sqlalchemy[asyncio] + asyncpg | 2.1.6 / 0.32 | psycopg2, SQLModel for serious code | legacy driver; SQLModel still 0.0.x beta |
| alembic | 1.20 | `create_all` at startup | no history, no review |
| pyjwt[crypto] (or joserfc) | 2.15 | python-jose | unmaintained since 2025-05, CVE history |
| pwdlib[argon2] | 0.3 | passlib | dead since 2020, breaks on bcrypt ≥ 4.1 and 3.13+ |
| structlog | 26.1 | ad-hoc `print` / f-string logs | |
| opentelemetry-sdk + instrumentation-fastapi/asyncpg | 1.45 / 0.66b1 | instrumentation-sqlalchemy on SQLAlchemy 2.1 | 0.66b1 supports < 2.1 only and silently does nothing |
| limits | 5.8 | slowapi | a decorator layer over `limits` that needs a `request` argument on every endpoint |
| httpx2 (tests, outbound) | 2.16 | httpx 0.28 for new code, `requests` in async code | Starlette now prefers httpx2; httpx unreleased since 2024-12 |
| time-machine | 3.6 | freezegun | slow, slower releases |
| pytest + pytest-asyncio / anyio plugin | 9.1 / 1.4 | async_asgi_testclient | unmaintained |
| ruff, mypy, import-linter | 0.17 / 2.4 / 2.15 | flake8 + isort + black | ruff covers all three |

uv's `exclude-newer = "7 days"` (Polar) guards against freshly published malicious releases, but needs lower bounds older than the window; FastAPI releases often enough that it pins you weeks back. Adopt it deliberately, not by default.

## §10 Tooling configuration

```toml
[tool.ruff.lint]
select = ["A","ARG","ASYNC","B","BLE","C4","DTZ","E","ERA","F","FAST","FBT","G","I","LOG","N","PERF","PIE",
          "PL","PT","PTH","RET","RSE","RUF","S","SIM","SLF","T20","TID","TRY","UP","W"]
ignore = ["PLR0913", "PLR0917"]      # FastAPI endpoints take many injected parameters
[tool.ruff.lint.flake8-tidy-imports.banned-api]
"datetime.datetime.now".msg = "Inject a Clock."
[tool.mypy]
strict = true
plugins = ["pydantic.mypy"]
warn_unreachable = true
enable_error_code = ["ignore-without-code", "redundant-expr", "truthy-bool"]
untyped_calls_exclude = ["opentelemetry.instrumentation.asyncpg"]   # untyped third-party constructor
```

Left out on purpose: `TC` (breaks FastAPI's runtime annotation resolution), `EM` (noise with structured exception constructors), `D` (docstrings everywhere restate code). Set `warn_required_dynamic_aliases = false` when models use `alias_generator`.

## §11 In-memory now, database later

When the task allows in-memory storage:
- **Keep:** the port, the version-guarded write, owner scoping, the `asyncio.Lock`, strict JSON, problem+json, auth, the race test, NUL/length rules (so the future database behaves the same), a `driver` setting with no default and the production guard, `/health/ready` (returns ok with no checks), and the `api` fixture parametrised over backends even with one param.
- **Skip:** Alembic, engine, Testcontainers, the column-mapping test (rule 17 has no table to compare), asyncpg instrumentation, `compose.yaml`.
- **Done** = the five checks green on the in-memory backend; say in the README that PostgreSQL is not yet covered.
- Layout: in-memory alone does not justify the layered layout (rule 2) — use the flat one.

Adding PostgreSQL later is one repository, one migration, one settings variant and one fixture param.

## §12 Logging and tracing

```python
logger = logging.getLogger("todo_api.todos")
logger.info("todo.created", extra={"todo_id": str(todo.id), "owner_id": owner_id})
# → {"event": "todo.created", "level": "info", "logger": "todo_api.todos", "todo_id": "…",
#    "owner_id": "user-alex", "timestamp": "…Z", "trace_id": "…", "span_id": "…"}
```

`configure_logging` uses `structlog.stdlib.ProcessorFormatter` with `ExtraAdder`, ISO UTC timestamps, a trace-context processor, and JSON (prod) or console (dev). The tracer and meter providers are installed globally once per process so trace ids always exist; `BatchSpanProcessor(OTLPSpanExporter())` only when `OTEL_EXPORTER_OTLP_ENDPOINT` is set. `FastAPIInstrumentor.instrument_app(app, excluded_urls="health/.*")` per app (undo with `uninstrument_app` in lifespan) and `AsyncPGInstrumentor().instrument()` once per process.

## §13 Idempotent create (when clients retry)

Table `idempotency_keys(owner_id, key, request_hash, status, response_json, created_at, PRIMARY KEY(owner_id, key))`. In one transaction: `INSERT … ON CONFLICT DO NOTHING RETURNING`; if it conflicts, compare `request_hash` (mismatch → 422 `IDEMPOTENCY_KEY_REUSED`) and replay the stored response; otherwise run the use case and store the response. Expire keys after 24 h with a scheduled job.

## §14 Zero-downtime migrations

- `env.py`: `context.execute("SET LOCAL lock_timeout = '5s'")` and `statement_timeout` inside the migration transaction; a blocked migration fails and the deploy step is retried, instead of every request queueing behind an `ACCESS EXCLUSIVE` lock.
- Expand → migrate → contract across releases: add the nullable column (or new table) → deploy code that writes both → backfill in batches (`UPDATE … WHERE id IN (SELECT … LIMIT 1000)`, commit per batch) → add `NOT NULL` via `CHECK … NOT VALID` + `VALIDATE CONSTRAINT` → drop the old column one release later.
- Indexes on live tables: `with op.get_context().autocommit_block(): op.create_index(..., postgresql_concurrently=True)`.
- Never rename a column in one step; add, dual-write, switch reads, drop.
- Extensions (`pg_trgm`) need elevated rights on managed PostgreSQL: keep `CREATE EXTENSION IF NOT EXISTS` in the first migration for local/test, and document it as an ops prerequisite (RDS: `rds_superuser`).

## §15 Outbox for cross-system effects

When a write must tell another system (webhook, queue, "job completed → update Sentinel"), insert `outbox(id uuid7, topic, payload jsonb, created_at, sent_at null)` in the **same transaction** as the aggregate. A worker selects unsent rows with `FOR UPDATE SKIP LOCKED`, delivers with retries and backoff, and sets `sent_at`; consumers dedupe by `id`. Never publish after commit from the request path — a crash between commit and publish loses the event.
