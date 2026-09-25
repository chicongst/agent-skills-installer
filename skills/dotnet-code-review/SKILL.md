---
name: dotnet-code-review
description: "Use when reviewing C#, .NET, or ASP.NET Core code — a class, file, diff, or module — or when the user pastes C# and asks for feedback, issues, or improvements without saying \"review\". Checks .NET slop (skipped tests, #pragma/NoWarn, `!` abuse, swallowed exceptions) and async, DI, EF Core, disposal, ASP.NET Core security, and logging pitfalls; reports BLOCKER/MAJOR/MINOR/NIT findings with fixes. Read-only. Not for other languages (use `code-review`), PR merge-readiness (use `pr-review`), scored multi-dimension audits (use `code-audit`), or applying fixes (use `dotnet-code-refactor`)."
---

# .NET Code Review

Review C#/.NET code the way a senior .NET engineer reviews a teammate's change: find real defects, rank them, propose concrete fixes. **Do not modify code** — if the user wants fixes applied, hand off to `dotnet-code-refactor`.

## Principles

1. **Effort follows blast radius, not line count.** A 20-line change to auth middleware deserves more scrutiny than a 500-line new read-only endpoint.
2. **Project convention beats general advice.** Read 2–3 neighboring files before calling something wrong. If the codebase uses repositories over `DbContext`, don't tell new code to drop them.
3. **Evidence or it isn't a finding.** Every finding cites `file:line`, the concrete failure (input → wrong result/crash/leak), and a fix snippet. If you can't point to it, don't claim it; ask instead.
4. **Don't guess intent.** If code references types you can't see or its purpose is unclear, ask the user (use AskUserQuestion if available, otherwise ask in plain text).

## Severity (canonical)

- **🔴 BLOCKER** — security hole, data loss/corruption, crash on reachable input, or broken contract. Must fix before merge.
- **🟠 MAJOR** — real bug, missing validation at a trust boundary, N+1 on a real path, or a design flaw that will bite soon. Fix before merge.
- **🟡 MINOR** — maintainability, clarity, or robustness issue worth fixing; may go to a tracked follow-up.
- **💭 NIT** — style/taste; one line, never dwell.

Uncertain items go under **Questions**, not a severity.

## Workflow

### Step 1 — Context and blast radius

State in 1–2 sentences what the code does (confirm with the user if unsure), then classify:

| Blast radius | Signals | Depth |
|---|---|---|
| **CRITICAL** | Auth/authz, middleware pipeline, `Program.cs` DI/config, EF migrations/model config, payments, shared kernel | Every line; trace callers |
| **HIGH** | Public API contracts, message consumers, background services, repositories used widely | Full catalogue; callers of changed signatures |
| **MEDIUM** | New feature following an existing pattern, internal service, tests | Standard pass |
| **LOW** | Renames, docs, logging text, formatting | Glance + slop scan |

With no surrounding code visible, say so: "No project context — reviewing against general .NET practice."

### Step 2 — Slop scan (cheap, always run)

Code that compiles but hides problems. Don't repeat what analyzers already report — flag the change that *suppresses* them. Severity = what it hides (a skipped test covering the changed path is MAJOR; a stray TODO is MINOR).

- **Disabled or hollow tests:** `[Fact(Skip = "...")]`, `[Theory(Skip = ...)]`, MSTest `[Ignore]`, NUnit `[Ignore("...")]`/`[Explicit]`, commented-out tests, `Assert.True(true)`, tests with no assertion, asserting only `Assert.NotNull(result)`.
- **Suppressed diagnostics:** `#pragma warning disable` without a matching `restore` or a reason; new `<NoWarn>` entries in `.csproj`/`Directory.Build.props`; `[SuppressMessage]` without `Justification`; `#nullable disable` or `<Nullable>disable</Nullable>` added; `<TreatWarningsAsErrors>` removed.
- **Null-forgiving abuse:** `!` used to silence a value that really can be null (`user!.Email` after a `FirstOrDefault`). `= null!;` on EF entity/DTO properties is an accepted idiom — prefer `required` (C# 11+) for new DTOs, but don't flag the idiom itself.
- **Swallowed failures:** empty `catch { }`; `catch (Exception) { return null; }` / `return false;`; logging then continuing as if the operation succeeded; `_ = SomeAsync();` discarding a task whose failure matters.
- **Shortcuts:** new `TODO`/`FIXME`/`HACK` in code claimed "done"; `.Result` added to make a method synchronous; secrets in `appsettings*.json` or code (use user-secrets locally, environment/Key Vault in deployed envs); copy-pasted blocks.

### Step 3 — .NET pitfall catalogue

Walk every section; write "OK" for sections checked with no findings. Typical severity in brackets — adjust to context.

**Async**
- `async void` outside event handlers — exceptions can't be caught by the caller and typically crash the process. [MAJOR]
- `.Result`, `.Wait()`, `.GetAwaiter().GetResult()` on incomplete tasks — deadlocks where a `SynchronizationContext` exists (WPF/WinForms/legacy ASP.NET); in ASP.NET Core, thread-pool starvation under load. [MAJOR]
- `CancellationToken` accepted but not passed on (to EF `ToListAsync(ct)`, `HttpClient`, `Task.Delay`), or not accepted on request paths. Controller/minimal-API `CancellationToken` parameters bind to `HttpContext.RequestAborted`. [MINOR; MAJOR on long-running work]
- `ConfigureAwait(false)`: expected in general-purpose **library** code; unnecessary in ASP.NET Core app code (no `SynchronizationContext`) — don't flag its absence there.
- Sequential `await` in a loop over independent I/O → `Task.WhenAll` (bounded, e.g. `Parallel.ForEachAsync` with `MaxDegreeOfParallelism`). Never `WhenAll` over the same `DbContext`.
- `await` inside `lock` doesn't compile; replacement `SemaphoreSlim` must be released in `finally`.
- Fire-and-forget `Task.Run` from a request that captures scoped services (`DbContext`) — they're disposed when the request ends. Use a queued `BackgroundService` that creates its own scope. [MAJOR]

**Dependency injection and lifetimes**
- Captive dependency: singleton depending on scoped/transient-with-state (e.g. singleton holding a `DbContext` or a typed `HttpClient`). Scope validation catches singleton→scoped only in Development. [MAJOR]
- `DbContext` is not thread-safe and is scoped by default. In singletons/`BackgroundService` use `IDbContextFactory<T>` or `IServiceScopeFactory.CreateScope()`. [MAJOR]
- `BuildServiceProvider()` called inside `ConfigureServices`/`Program.cs` — creates a second container with duplicate singletons. [MAJOR]

**HttpClient**
- `new HttpClient()` per call → socket exhaustion; a single long-lived static instance → stale DNS unless `SocketsHttpHandler.PooledConnectionLifetime` is set. Prefer `IHttpClientFactory` (named/typed clients). [MAJOR]
- No timeout/resilience policy on outbound calls where the project uses one elsewhere (e.g. `AddStandardResilienceHandler`). Follow project convention.

**EF Core**
- N+1: query or lazy-loaded navigation inside a loop → `Include` or a `Select` projection. [MAJOR on real paths]
- `ToList()`/`AsEnumerable()` before `Where`/`Select` → the filter runs in memory after loading every row. [MAJOR]
- EF Core 3.0+ throws on untranslatable expressions except in the final `Select`; a method call there runs client-side — fine for formatting, wrong if it drags whole entities over the wire.
- Read-only queries tracked by default → `AsNoTracking()` (or project to a DTO). [MINOR]
- `SaveChanges()` inside a loop → one round trip per item; call once after the loop, or use `ExecuteUpdateAsync`/`ExecuteDeleteAsync` (EF Core 7+) for set-based changes. [MAJOR on large sets]
- Multiple collection `Include`s → cartesian explosion; consider `AsSplitQuery()`.
- New filter/sort/join columns without `HasIndex` in model config or a migration. [MAJOR on large tables]
- Unbounded queries (no `Take`/paging) on user-facing lists.
- Migration changes: review generated SQL (`dotnet ef migrations script`) for drops, renames emitted as drop+add, and locking on large tables. [CRITICAL radius]

**Disposal**
- `IDisposable` created and not disposed → `using` declaration; `IAsyncDisposable` (`DbContext`, streams, `Utf8JsonWriter`…) → `await using`. [MAJOR for connections/streams]
- Disposing something the DI container owns (injected services). [MAJOR]

**Nullability and exceptions**
- Nullable reference types off in new projects, or new warnings (CS86xx) ignored. [MINOR]
- `throw ex;` resets the stack trace → `throw;`, or wrap with `new XException("context", ex)`. [MINOR; MAJOR if it hides a production bug's origin]
- Catching `OperationCanceledException` as an error (logs an error and records a 500 for a normal client disconnect).

**ASP.NET Core**
- Authorization: new endpoint without `[Authorize]`/`RequireAuthorization()` where the project has no fallback policy; stray `[AllowAnonymous]`; checks that the user is authenticated but not that they **own** the resource (IDOR). [BLOCKER]
- Over-posting: binding EF entities directly from the request body → bind an input DTO and map explicitly. [MAJOR; BLOCKER if it lets users set roles/prices/owner]
- Validation: `[ApiController]` returns a 400 `ValidationProblemDetails` automatically; minimal APIs don't validate DataAnnotations unless the project opts in (`AddValidation()` in .NET 10+, FluentValidation, or an endpoint filter). `[ApiController]` returns 400 even for semantically invalid input: follow the project's existing 400/422 convention; if there is none, raise it as a Question, not a finding.
- Antiforgery: cookie-authenticated form posts need antiforgery (Razor Pages validate automatically; MVC needs `[ValidateAntiForgeryToken]` or the auto-validate filter; minimal-API form binding needs `AddAntiforgery()` + `UseAntiforgery()`). Pure bearer-token APIs don't.
- Errors: stack traces or `ex.Message` returned to clients in production → `AddProblemDetails()` + `UseExceptionHandler`. [MAJOR]
- Other injection points: `FromSqlRaw`/`ExecuteSqlRaw` with interpolated or concatenated input → `FromSql`/`FromSqlInterpolated` or parameters [BLOCKER]; `Path.Combine(root, userInput)` — a rooted `userInput` discards `root`, and `..` escapes it; validate the resolved full path stays under `root` [BLOCKER]; `System.Random` for tokens → `RandomNumberGenerator` [BLOCKER]; hand-rolled password hashing → `PasswordHasher<T>` or a vetted KDF.

**Logging**
- String interpolation in log calls (`_logger.LogInformation($"Order {id}")`) loses structured properties and formats even when the level is off → message template `LogInformation("Order {OrderId} placed", id)` (analyzer CA2254). Hot paths: `[LoggerMessage]` source generator. [MINOR]
- Passwords, tokens, connection strings, or PII in log arguments or logged request bodies. [BLOCKER for secrets]
- Exception passed as a template argument instead of the `exception` parameter (`LogError(ex, "...")`).

**General correctness and testability**
- `DateTime.Now` in logic → `DateTime.UtcNow` or injected `TimeProvider` (.NET 8+) so it's testable.
- String comparison without `StringComparison.Ordinal`/`OrdinalIgnoreCase`; `ToLower()` equality.
- Non-thread-safe collections (`Dictionary`, `List`) mutated in singletons → `ConcurrentDictionary` or a lock.
- `double`/`float` for money → `decimal`.
- Tests: new branches covered (happy, error, edge)? Over-mocked `DbContext` or EF InMemory provider for query tests misses real SQL translation — prefer SQLite in-memory or a Testcontainers database when the project does. Tests sharing state across `[Fact]`s.

### Step 4 — Convention check

Compare with 2–3 sibling files: naming, layering (controller → service → repository or handlers), result/error style, DI registration location, async suffixes, test naming. A deviation from a core codebase pattern is MAJOR; a local inconsistency is MINOR. When general .NET advice conflicts with the project's pattern, raise it as a Question or a follow-up, not a finding.

If you can run commands, `dotnet build` (look for new warnings), `dotnet test`, and `dotnet list package --vulnerable` give evidence; mark findings you reproduced `[verified]`.

### Step 5 — Report

No filler praise; genuine strengths go in "Checked OK".

````markdown
# .NET Code Review — [file / feature]

**Blast radius:** CRITICAL | HIGH | MEDIUM | LOW
**Findings:** Blocker x · Major y · Minor z · Nit w
**Verdict:** REQUEST CHANGES | APPROVE WITH COMMENTS | APPROVE | NEEDS DISCUSSION

## Summary
[2–4 sentences: what the code does, the main risk, why this verdict]

## Findings
### 🔴 BLOCKER
#### [B-1] [Short title]
**Location:** `path/File.cs:42-48`
**Problem:** [concrete defect]
**Impact:** [what happens in production]
**Fix:**
```csharp
// before
...
// after
...
```
### 🟠 MAJOR
[same fields, M-1…]
### 🟡 MINOR
[same fields; may group findings sharing a cause]
### 💭 NIT
- [one line each]

## Questions
- [things only the author can answer]

## Checked OK
- [section]: [what was verified]

## Follow-up (out of scope)
- [tech debt noticed but unrelated to this change]
````

Omit empty severity sections. For a short snippet outside a PR, keep the same headings but drop Verdict.

**Verdict rules** (follow from the severity definitions):
- **REQUEST CHANGES** — any BLOCKER or MAJOR.
- **APPROVE WITH COMMENTS** — MINOR findings only (plus NITs/questions).
- **APPROVE** — NITs or nothing.
- **NEEDS DISCUSSION** — the approach itself is wrong or unclear; line-level findings would be premature.

## Special situations

- **Large diff (> ~500 lines):** say so, review by project/folder in passes, CRITICAL-radius files first.
- **Single dimension requested ("security only"):** do that, but still run the Step 2 slop scan.
