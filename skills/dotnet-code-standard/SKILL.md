---
name: dotnet-code-standard
description: Use when writing, scaffolding, or extending C# / .NET / ASP.NET Core backend code — new APIs, services, workers, solutions, csproj/Directory.Build.props/.editorconfig setup — or when the user asks for production-grade, "chuẩn", large-project-quality .NET code. Not for reviewing existing C# (use `dotnet-code-review`), restructuring existing code with identical behavior (use `dotnet-code-refactor`), or other languages (use `nodejs-code-standard` for Node, `python-code-standard` for Python).
---

# .NET Code Standard

Write .NET the way the most-starred .NET application repos do: layered projects whose references enforce the architecture, one handler per use case, Result for expected failures, ProblemDetails on the wire, authenticated and owner-scoped data, validated configuration, observable dependencies, and a build where warnings are errors. **"It compiles" is not done. Done = `dotnet build` with 0 warnings and `dotnet test` green, including against the real database.**

Project conventions and CLAUDE.md win over this skill. Read 2–3 neighbouring files before adding code to an existing solution.

## Sources (stars checked 2026-10-26)

| Repo | ★ | What we take from it |
|---|---|---|
| dotnet/aspnetcore | 38k | Minimal APIs, `TypedResults`/`Results<…>`, ProblemDetails, `IExceptionHandler`, built-in OpenAPI, rate limiting |
| jasontaylordev/CleanArchitecture | 21k | `src/{Domain,Application,Infrastructure,Web}`, use-case folders, `AddXxx()` per layer, `TimeProvider`, ADRs |
| ardalis/CleanArchitecture | 19k | Result pattern mapped to HTTP, xUnit v3 + Testcontainers, CPM transitive pinning, `.slnx` |
| DapperLib/Dapper · dotnet/efcore | 18k · 15k | `IEntityTypeConfiguration<T>`, migrations in Infrastructure, concurrency tokens |
| kgrzybek/modular-monolith-with-ddd | 14k | Architecture tests for layer rules |
| dotnet/eShop | 11k | `MapXxxApi()` groups, `global.json` + Microsoft.Testing.Platform, OpenTelemetry service defaults, `LoggerMessage` |

The reference solution `examples/TodoApi/` was scored by a two-role review council (principal architect + quality/security reviewer); its findings are folded into the rules below.

## Rules (non-negotiable)

**Solution & structure** — tree, lifetimes and HTTP contract: `examples/TodoApi/README.md`
1. `.slnx`, `src/` + `tests/`, `global.json` (SDK + test runner), `Directory.Build.props`, `Directory.Packages.props` (CPM + `CentralPackageTransitivePinningEnabled`), `.editorconfig`, `dotnet-tools.json`, `compose.yaml` for local dependencies, `docs/decisions/` for ADRs. When the task allows in-memory storage, follow patterns §12 for what to keep and what to skip.
2. Four projects `<App>.Domain` → `<App>.Application` → `<App>.Infrastructure` → `<App>.Api` when **two or more hold today** (planned work does not count): a state machine or cross-field invariants, more than one storage backend, more than one entry point (API + worker), a team larger than two. Otherwise one Api project with feature folders — say which and why in one line. Project references are the architecture; architecture tests cover what references cannot.
3. Domain has **zero** package references. Entities protect invariants: private constructor, `private init`, static `Create(...)` returning `Result<T>`, behaviour methods. A `record` entity is fine for `with`, but never rely on its value equality — detect "no change" by comparing `Version`.
4. Application: one folder per use case holding the command/query record and its `sealed` handler (`UpdateTodo/UpdateTodoHandler.cs` → `UpdateTodoCommand` + `UpdateTodoHandler.HandleAsync(command, ct)`). Every handler takes a command/query record. Ports live in `Application/Abstractions`. Register in `AddApplication()`.
5. Infrastructure implements ports; repositories are `internal sealed`. `AddInfrastructure(configuration)` picks the implementation. Unit tests use a fake written in the test project that implements the whole port (no `NotSupportedException` stubs). Unit tests reference Infrastructure at most, never Api.
6. Api is the composition root: `Program.cs` only wires and orders middleware; HTTP services go in `AddApi()`; endpoints in `<Resource>/<Resource>Endpoints.cs` via `MapGroup`; request/response contracts are records with a static `From(...)` mapper. Never return domain entities.
7. Constructor injection (primary constructors). Lifetimes on purpose: stateful in-memory stores singleton; DbContext, repositories, handlers scoped. No static mutable state, no service locator in business code.

**Security**
8. Authentication on by default: `AddAuthentication().AddJwtBearer()` from configuration, one policy `RequireAuthenticatedUser()` set as **both default and fallback** (`RequireAuthorization()` on a group uses the *default* policy, so a fallback-only rule silently skips those endpoints), `AllowAnonymous()` only on health. Ownership lives in the aggregate (`OwnerId` from the token subject) and every repository query filters by it; another owner's resource is **404**, not 403. That policy also requires the subject claim (`RequireClaim(ClaimTypes.NameIdentifier)`) so a token without one gets 403, not 500. Roles/scopes are named policies on endpoint groups. Optimistic concurrency then protects one owner's devices from each other; editing shared between users needs an explicit sharing model.
9. Writes are rate limited per user (`AddRateLimiter`, 429 ProblemDetails with `type` and `Retry-After`; the limit is per replica — say so in an ADR). Creates called by retrying clients (partner integrations, message consumers, mobile offline sync) accept an `Idempotency-Key` (patterns §10); for a first-party UI, record the decision to skip it in an ADR. Version the URL (`/v1`) or use `Asp.Versioning.Http` before exposing an API to partners; internal-only APIs may stay unversioned.

**Errors**
10. Expected failures → `Result<T>` with `DomainError(Kind, Code, Message, Field, Details)`. Exceptions only for bugs and infrastructure faults. `ErrorKind` lists only kinds something actually produces.
11. Every error is RFC 9457 ProblemDetails with a stable `code`: domain errors via one `Problems.From`, framework errors (401, 404, 405, 413, 415, 429) via `CustomizeProblemDetails` mapping status → code, bad JSON via `IExceptionHandler` turning `JsonException` into `errors[<path>]` with a fixed detail. `traceId` is added by the framework — don't add it yourself. Never leak exception or type names.
12. Domain errors carry a `Kind`, never an HTTP status; the Api maps kind → status in one place.

**Input/output**
13. JSON is strict: `UnmappedMemberHandling.Disallow`, `AllowDuplicateProperties = false`, a **strict enum converter** that accepts only exact camelCase names (`JsonStringEnumConverter` also accepts `"medium,high"` flag combinations and other casings — an undefined value gets stored and breaks every later read), plus `Enum.IsDefined` in the domain. `DateOnly` for dates, body size limit, `ThrowOnBadRequest = true`.
14. PATCH distinguishes absent from null (`PatchField<T?>` + converter; nullable all the way, no `!`). Query-string enums parsed from an explicit map — minimal-API enum binding accepts `"1"`.
15. Lists are bounded (default 20, max 100), deterministic (tie-break on `Id`), nulls last in both directions. Offset + `total` for small per-user lists; keyset (`?after=`) for large or partner-facing ones. Substring search on Postgres gets a `pg_trgm` GIN index.

**Data**
16. EF Core: `IEntityTypeConfiguration<T>` per entity with explicit names/lengths/indexes; `AsNoTracking` reads. Full-entity writes: `Attach`, mark modified, set the concurrency token's `OriginalValue = expectedVersion`, `SaveChangesAsync`, catch `DbUpdateConcurrencyException` — every column is included automatically. `ExecuteUpdateAsync` only for set-based or deliberately partial updates. On a miss, return the current version from the same repository call.
17. Migrations via `dotnet ef`, deployed as a migration bundle in the pipeline; never `EnsureCreated`, never at app start in production. Design-time factory reads its connection from an environment variable — no credentials in code.
18. One `DbContext` per scope and never two queries on it concurrently. Parameterised queries only; escape `LIKE` wildcards.
19. Shared mutable resources use optimistic concurrency: `Version` + `ETag` + required `If-Match` (missing or `*` → 428, weak → 412, malformed → 400, stale → 412 with `currentVersion`).

**Async**
20. `async` all the way, `CancellationToken` on every async signature and passed down. No `.Result`, `.Wait()`, `async void`. Outbound HTTP via `IHttpClientFactory` + `AddStandardResilienceHandler()`.

**Config, time, logging, operations**
21. Options classes with `SectionName`, `ValidateDataAnnotations().ValidateOnStart()`. **No default may select a non-durable or insecure behaviour** (in-memory storage, disabled auth): those values live only in `appsettings.Development.json`; a missing production value stops the app at boot. Settings that decide registrations are loaded and validated eagerly. Validate `JwtBearerOptions` at start too — Authority **or** signing keys present — which keeps `dotnet user-jwts` working in Development (patterns §4). Secrets from environment/secret store only.
22. Inject `TimeProvider`; never `DateTime.Now/UtcNow` in logic. IDs from `Guid.CreateVersion7(now)`.
23. `[LoggerMessage]` methods (CA1848 on) for business events and for every 412/conflict. JSON console in production. OpenTelemetry logs/metrics/traces with **every outbound dependency instrumented** (ASP.NET Core, HttpClient, `Npgsql.OpenTelemetry`); OTLP only when configured. `/health/live` (no checks) and `/health/ready` (dependency checks tagged `ready`).

**Build & tooling**
24. `Nullable`, `TreatWarningsAsErrors`, `AnalysisLevel=latest-recommended`, `EnforceCodeStyleInBuild`, `GenerateDocumentationFile` (needed for IDE0005) with `NoWarn CS1591` as the **only** allowed suppression. File-scoped namespaces, `_camelCase` fields, `Async` suffix as `.editorconfig` errors/warnings. `Migrations/` marked `generated_code = true`. No `#pragma warning disable` to get green.

**Testing**
25. xUnit v3 on Microsoft.Testing.Platform, two projects: `<App>.UnitTests` (Domain/, Application/ with fakes, Architecture/) and `<App>.IntegrationTests` (Api/, Persistence/, Fixtures/). The HTTP contract is an abstract test class run against **every** storage backend (in-memory and PostgreSQL via Testcontainers + real migrations; never EF InMemory). Isolate tests with a fresh `WebApplicationFactory` and a unique owner id, not table truncation. Mandatory: a parallel test proving exactly one of N concurrent writers wins, 401, cross-owner 404, and each failure status the API can actually return. Body-limit 413 needs a Kestrel smoke test: `factory.UseKestrel(0); factory.StartServer();` then `factory.CreateClient()` (TestServer ignores Kestrel limits). Every ProblemDetails test asserts the `code`. Names `Method_Scenario_Expected`; pass `TestContext.Current.CancellationToken`.

**Docs**
26. Every non-obvious structural decision gets a short ADR. The README carries run commands, tree, dependency table, lifetimes, HTTP contract and "where does new code go". No comments that restate code.

## Red flags — stop and fix

| You catch yourself… | Do instead |
|---|---|
| A default that silently picks in-memory storage or skips auth | Required setting; dev value only in `appsettings.Development.json` |
| Endpoints without `RequireAuthorization` / no fallback policy | Fallback policy + ownership filter in the repository |
| `JsonStringEnumConverter` as "strict enums" | Strict converter + `Enum.IsDefined` in the domain |
| A hand-written column list in a full-entity update | Concurrency token + `SaveChangesAsync` |
| Re-reading the row after a failed write to get its version | Return it from the repository call |
| API tests only against the in-memory store | Same contract class against PostgreSQL |
| `/health` checking the DB used as liveness | `/health/live` + `/health/ready` |
| An `IXxxService` with every action / handlers taking loose primitives | One handler per use case, one command record each |
| `throw new NotFoundException()` for a normal miss | Return `TodoErrors.NotFound(id)` |
| `DateTime.UtcNow` / `Guid.NewGuid()` in a handler | `TimeProvider` / `Guid.CreateVersion7(now)` |
| `_logger.LogInformation($"...")` | `[LoggerMessage]` partial method |
| `Task.WhenAll` on two queries of one `DbContext` | Await in sequence |
| A connection string with a password in code or README | Environment variable / user-secrets / `${VAR:?}` in compose |
| `dotnet run` to test Production behaviour | `--no-launch-profile` — `launchSettings.json` forces Development |
| Root namespace that shadows the BCL (`Tasks`, `Threading`, `Collections`) | Product name: `TodoList.*`, `Billing.*` |
| `appsettings.json` shipping empty placeholders (`"Authority": ""`) | Omit the key; validate on start |
| Adding MediatR / AutoMapper / FluentAssertions 8 | Direct handlers, `From(...)`, xUnit `Assert` or Shouldly (patterns §9) |

## Reference

- Reference solution: `examples/TodoApi/` — `README.md` first, then `docs/decisions/`.
- Before/after patterns, analyzer pitfalls and package licences: `references/patterns.md`.

## Done checklist

- [ ] Project split justified (rule 2); references match the dependency rule; architecture tests pass
- [ ] Auth fallback policy, ownership filter, rate limit on writes
- [ ] One handler + command per use case; ports in Application; repositories internal
- [ ] Strict JSON (unknown, duplicate, enum) and ProblemDetails with `code` for every error path
- [ ] Optimistic concurrency via concurrency token; bounded deterministic lists
- [ ] No insecure/non-durable defaults; options validated at boot; migrations as a bundle
- [ ] `TimeProvider`, `[LoggerMessage]`, OpenTelemetry incl. database, live/ready health
- [ ] Unit tests + HTTP contract on every backend + race test + 401/404/412/428
- [ ] `dotnet build` → 0 warnings, `dotnet test` → all green — show the output, do not claim it
