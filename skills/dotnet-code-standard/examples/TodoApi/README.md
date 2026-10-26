# TodoApi — reference .NET 10 structure

ASP.NET Core minimal APIs, JWT auth with per-user ownership, EF Core + PostgreSQL (or in-memory for development), OpenTelemetry, xUnit v3 on Microsoft.Testing.Platform, Testcontainers.

## Run

```bash
dotnet build                                   # warnings are errors; analyzers + code style enforced
dotnet test                                    # needs Docker (PostgreSQL via Testcontainers)

# Development: in-memory storage (appsettings.Development.json) + a local signed token.
# Run user-jwts first: without an Authority or signing keys the app refuses to start.
dotnet user-jwts create --project src/Todo.Api # prints a bearer token, stores dev signing keys in user-secrets
dotnet run --project src/Todo.Api

# PostgreSQL locally
export TODO_DB_PASSWORD=change-me
docker compose up -d postgres
export Storage__Driver=Postgres
export Storage__ConnectionString="Host=localhost;Database=todo;Username=todo;Password=$TODO_DB_PASSWORD"
TODO_DESIGN_CONNECTION="$Storage__ConnectionString" dotnet ef database update --project src/Todo.Infrastructure
dotnet run --project src/Todo.Api

# Schema changes and deployment
TODO_DESIGN_CONNECTION="Host=localhost;Database=todo" \
  dotnet ef migrations add <Name> --project src/Todo.Infrastructure --output-dir Persistence/Migrations
TODO_DESIGN_CONNECTION="Host=localhost;Database=todo" \
  dotnet ef migrations bundle --project src/Todo.Infrastructure -o artifacts/efbundle
./artifacts/efbundle --connection "<production connection string>"   # a pipeline step, never at app start
```

`Storage:Driver` and `Authentication:Schemes:Bearer:Authority` have no defaults. Production must set both; a missing value stops the app at boot (verified with `--no-launch-profile`).

## Folder structure

```
TodoApi.slnx
global.json                      # pins SDK + Microsoft.Testing.Platform runner
Directory.Build.props            # net10.0, Nullable, TreatWarningsAsErrors, AnalysisLevel, code style in build
Directory.Packages.props         # central package versions + transitive pinning
.editorconfig                    # style + naming rules; Migrations marked generated
dotnet-tools.json                # dotnet-ef pinned per repo
compose.yaml                     # local PostgreSQL
docs/decisions/                  # ADR-001..005: why it looks like this
src/
├── Todo.Domain/                 # no package references at all
│   ├── Common/                  # Result<T>, DomainError, ErrorKind, PatchField<T>
│   └── Todos/                   # TodoItem (immutable record + rules), TodoDraft, TodoChanges, TodoErrors, enums
├── Todo.Application/            # use cases; Domain + Microsoft.Extensions.*.Abstractions only
│   ├── Abstractions/            # ITodoRepository (port), WriteResult, Page<T>, PageRequest
│   ├── Todos/
│   │   ├── CreateTodo/CreateTodoHandler.cs     # CreateTodoCommand + CreateTodoHandler
│   │   ├── GetTodo/ · ListTodos/ · UpdateTodo/ · CompleteTodo/ · ReopenTodo/ · DeleteTodo/
│   │   ├── VersionedWrite.cs    # shared optimistic-concurrency steps
│   │   └── TodoLog.cs           # [LoggerMessage] events
│   └── DependencyInjection.cs   # AddApplication()
├── Todo.Infrastructure/         # EF Core, Npgsql; implements the ports
│   ├── Persistence/             # TodoDbContext, Configurations/, Migrations/, design-time factory
│   ├── Todos/                   # PostgresTodoRepository, InMemoryTodoRepository (both internal)
│   ├── StorageOptions.cs        # required driver, validated at boot
│   ├── HealthCheckTags.cs
│   └── DependencyInjection.cs   # AddInfrastructure(configuration)
└── Todo.Api/                    # composition root + HTTP only
    ├── Program.cs               # wiring and middleware order, nothing else
    ├── DependencyInjection.cs   # AddApi(): JSON, ProblemDetails, auth, rate limits, OpenAPI
    ├── Todos/                   # TodoEndpoints (MapGroup), TodoContracts, TodoListQueryParser
    ├── Http/                    # Problems, GlobalExceptionHandler, ETag, StrictEnumConverter, PatchFieldJsonConverter
    ├── Auth/                    # owner id from claims, rate-limit policies
    ├── Health/                  # /health/live, /health/ready
    └── Observability/           # OpenTelemetry logs/metrics/traces incl. Npgsql
tests/
├── Todo.UnitTests/              # Domain/, Application/ (FakeTodoRepository), Architecture/
└── Todo.IntegrationTests/       # Api/ (same contract on in-memory AND PostgreSQL), Persistence/, Fixtures/
```

## Dependency rule

```
Todo.Api ──▶ Todo.Application ──▶ Todo.Domain
   │                ▲
   └──▶ Todo.Infrastructure (implements Application.Abstractions)
```

| Project | References | Must never reference | Enforced by |
|---|---|---|---|
| Domain | nothing | any package, any other project | project file + architecture tests |
| Application | Domain, `Microsoft.Extensions.*.Abstractions` | EF Core, ASP.NET Core, Npgsql, Infrastructure | project file + architecture tests |
| Infrastructure | Application, EF Core, Npgsql | Api | project file + architecture tests |
| Api | Application, Infrastructure | — (composition root) | — |

## How instances are created

| Service | Lifetime | Registered in | Why |
|---|---|---|---|
| `TimeProvider` | singleton | `AddApplication` (`TryAdd`) | tests use `FakeTimeProvider` |
| Handlers | scoped | `AddApplication` | one per request; depend on the scoped repository |
| `InMemoryTodoRepository` | singleton | `AddInfrastructure` | holds state; guarded by a `Lock` |
| `TodoDbContext` + `PostgresTodoRepository` | scoped | `AddInfrastructure` | DbContext is not thread-safe |
| Auth, rate limiter, ProblemDetails, JSON | framework | `AddApi` | HTTP concerns stay in Api |

No `new` of infrastructure outside `DependencyInjection.cs` and tests. No static mutable state. Every integration test builds its own `WebApplicationFactory` and uses a fresh owner id, so tests never share data even on one PostgreSQL container.

## HTTP contract

| Situation | Status | `code` |
|---|---|---|
| No or invalid token | 401 | `UNAUTHORIZED` |
| Body: unknown field, duplicate key, wrong type, numeric/comma/miscased enum, impossible date | 400 | `VALIDATION_FAILED` + `errors` |
| Domain rule (blank title, too long, empty PATCH) | 400 | `VALIDATION_FAILED` + `errors.<field>` |
| Unknown todo, another user's todo, malformed GUID in the route | 404 | `TODO_NOT_FOUND` / `NOT_FOUND` |
| Token without a subject claim | 403 | `FORBIDDEN` |
| Write without `If-Match`, or `If-Match: *` | 428 | `PRECONDITION_REQUIRED` |
| Stale or weak ETag | 412 | `VERSION_MISMATCH` (+ `currentVersion` when stale) |
| Body over 1 MB (Kestrel only) | 413 | `PAYLOAD_TOO_LARGE` |
| More than 60 writes/min per user (per replica) | 429 + `Retry-After` | `TOO_MANY_REQUESTS` |
| Unhandled exception | 500 | `INTERNAL_ERROR`, no exception text |

All errors are RFC 9457 ProblemDetails with `traceId`.

## Request flow — `PATCH /todos/{id}`

1. Kestrel caps the body; the fallback policy rejects anonymous calls; the per-user rate limiter runs.
2. System.Text.Json (strict converters) binds `UpdateTodoRequest`; `PatchField<T>` tells absent from `null`.
3. `TodoEndpoints.UpdateAsync` parses `If-Match` and builds `UpdateTodoCommand(ownerId, id, version, changes)`.
4. `UpdateTodoHandler` loads the owner's todo, checks the version, calls the pure `TodoItem.Apply`, then `UpdateAsync(next, expectedVersion)`.
5. `PostgresTodoRepository` saves with `Version` as concurrency token → one `UPDATE … WHERE id = @id AND version = @expected`; a miss returns `WriteResult.Mismatch(current)` in the same call.
6. `Problems.From` maps `ErrorKind` → 400/404/412; conflicts are logged as `VersionConflict` warnings.

## Where does new code go?

| You are adding… | Put it in |
|---|---|
| A business rule | `Todo.Domain/Todos/TodoItem.cs` (+ error in `TodoErrors`) and a test in `UnitTests/Domain` |
| A new action | `Todo.Application/Todos/<Action>/<Action>Handler.cs` (command + handler), register in `AddApplication`, map in `TodoEndpoints` |
| A new storage backend | `Todo.Infrastructure/Todos/<Name>TodoRepository.cs` (internal), select it in `AddInfrastructure`, run the API contract against it |
| A schema change | `Persistence/Configurations`, then `dotnet ef migrations add` |
| A config value | options class with `SectionName` + validation, `ValidateOnStart()` |
| A role or partner scope | a named authorization policy on the endpoint group |
| A new resource ("projects") | `Domain/Projects`, `Application/Projects/<UseCase>/`, `Infrastructure/Projects`, `Api/Projects` |
| A decision someone will question later | `docs/decisions/ADR-00N-<title>.md` |
