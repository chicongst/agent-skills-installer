---
name: dotnet-code-refactor
description: Use when restructuring, cleaning up, or simplifying existing C#, .NET, or ASP.NET Core code with identical behavior — including after a `dotnet-code-review` when the user says "apply the fixes". One smell at a time, SAFE/RISKY/DANGEROUS risk, characterization tests first, and .NET traps (LINQ deferred execution, async, records, EF Core translation, DI lifetimes). Modifies code. Not for other languages (use `refactor`), review-only feedback (use `dotnet-code-review`), bug fixes (use `fix-bug` or `debug`), or speed work (use `performance-review`).
---

# .NET Code Refactor

Act as a senior .NET engineer improving code others depend on, one verified step at a time.

## Core principles

1. **Refactoring = no observable behavior change**: same results, exceptions and messages, side effects, public API, JSON shape, query results. New validation/pagination/transactions, changed messages, input trimming, or a bug fix is a **behavior change** — recommend it separately; never slip it in.
2. **One smell, smallest step**, build and test between steps. Refactoring and feature work never share a change.
3. **Project convention beats generic best practice.** Read neighboring files, `.editorconfig`, and `Directory.Build.props` (`Nullable`, `TreatWarningsAsErrors`, analyzers). Keep the existing folder layout; if none, group by feature.
4. **No safety net, no RISKY refactor.** Write characterization tests first, or stop.
5. **DANGEROUS work waits for the user's explicit yes.** Ask (use AskUserQuestion if available, otherwise ask in plain text).

## Workflow

### Step 1 — Diagnose

State what the code does and who calls it; if you can't, ask. Given a `dotnet-code-review` report, only its behavior-neutral findings belong here; the rest are behavior changes (principle 1).

| Smell | .NET signal | Refactoring |
|---|---|---|
| Long method | > ~50 lines, several jobs | Extract Method / local function |
| God service | 6+ constructor dependencies, unrelated methods | Extract Class along one responsibility |
| Long parameter list / data clump | > 4–5 params; same group travels together | Parameter object (`record`) |
| Duplicate code | Same logic in 2+ places | Extract Method — grep for an existing helper first |
| Primitive obsession | `string email`, `decimal` money without currency | Value object (`readonly record struct`) |
| Deep nesting | 4+ levels of `if` | Guard clauses / early return |
| Repeated type switch | Same `switch` on an enum in several methods | Polymorphism; a lone switch → at most a switch expression |
| Scattered config reads | `config["Smtp:Host"]` in many classes | Bound `IOptions<T>` |
| Speculative generality | One-implementation interface with no test double | Inline it |

**Interfaces and wrappers:** extract an interface only for a real seam (a test double you will write, a second implementation); wrap a third-party dependency only where the wrapper adds value (narrower interface, error translation, test seam) — inline pass-through proxies.

For "refactor this whole file": propose the top 2–3 smells and ask which first.

### Step 2 — Classify risk

| Level | Examples | Handling |
|---|---|---|
| **SAFE** | IDE rename of a private/local symbol; Extract Method with clear inputs/outputs; inline a single-use local; guard clauses | Proceed on existing build + tests |
| **RISKY** | Public renames; Extract Class / Move Method; class → record; loop ↔ LINQ; sync → async on a private/internal method (public signatures = behavior change); collection type changes; extracting an interface; DI registrations | Characterization tests first, full suite after |
| **DANGEROUS** | Auth/authz, money, EF model config/migrations/hot queries, transactions/locks, public API/DTO contracts, message consumers, lifetimes of stateful services | Stop, explain risk and a safer breakdown, wait for approval |

A "private" rename is RISKY if the name reaches reflection, Razor, config binding, EF column conventions, or JSON keys (System.Text.Json uses property names). Grep the string, not just the symbol.

### Step 3 — Test safety net

1. Run the baseline: `dotnet build`, then `dotnet test` (narrow with `--filter "FullyQualifiedName~OrderService"`). Red baseline → stop and ask.
2. Tests that only `Verify(...)` mocks or assert `NotNull` count as none.
3. Characterization test: assert what the code **actually** returns or throws (exact exception type) today, bugs included:

```csharp
[Fact]
public void Discount_NonPremiumUser_ReturnsZero() =>
    Assert.Equal(0m, Pricing.Discount(new User(IsPremium: false), total: 500m));
```

EF Core query refactors: characterize on the production database engine (Testcontainers); SQLite in-memory is a fallback that hides async-timing bugs; the InMemory provider never translates to SQL. Bug found while characterizing → list it under "Behavior changes recommended"; don't fix it here.

### Step 4 — Plan

```markdown
## Refactor Plan
**Files:** `src/Orders/OrderService.cs`
**Smell → refactoring:** [e.g. Long method → Extract Method]
**Risk:** SAFE / RISKY / DANGEROUS
**Safety net:** ✅ sufficient / ⚠️ weak — adding characterization tests / ❌ none — adding
**Steps:** 1. [atomic, builds and passes on its own] 2. …
```

Wait for confirmation on RISKY/DANGEROUS plans; clear SAFE work may proceed.

### Step 5 — Apply

1. One step → `dotnet build` → `dotnet test` → next step.
2. Rename with the IDE/Roslyn rename, then do the Step 2 string grep.
3. Format touched files only, with the project's `.editorconfig`/analyzers: `dotnet format --include src/Orders/OrderService.cs`.
4. Never silence a new warning (`#pragma`, `<NoWarn>`, `!`) — it means the step changed something. No package upgrades or namespace moves on the side.
5. **A step fails unexpectedly:** undo only that step (restore the previous text, or `git revert` its commit) — never "fix" the tests. Ask before `git stash` or `git checkout -- <file>`; never `git reset`. Outdated branch or conflicts → ask the user; don't rebase or merge.

### Step 6 — Verify and report

Full `dotnet build` (warnings ≤ baseline) and `dotnet test`; review the diff and revert anything outside the plan.

```markdown
# Refactor Report — [file/feature]
**Smell → refactoring:** … **Risk:** …
## Changes
- [one line per change/file]
## Verification
- Build: ✅ (warnings: before N → after N)   Tests: ✅ X passed (Y characterization tests added)
- Behavior evidence: [input → same output before and after]
## Deliberately not changed
- [tempting cleanups or deferred smells, and why]
## Behavior changes recommended (not applied)
- [🔴 BLOCKER / 🟠 MAJOR / 🟡 MINOR / 💭 NIT] [title] — `file:line` — [problem] → [proposed separate change]
```

Omit empty sections. Severities are defined as in `dotnet-code-review`.

User insisted on no tests → open the report with "No safety net — behavior not verified."

## .NET behavior-preservation traps

**LINQ deferred execution.** An extracted `IEnumerable<T>` query re-runs on every enumeration — side effects repeat and results track source changes. Adding/removing `.ToList()` moves *when* (for `IQueryable`, *where*) it runs.

```csharp
IEnumerable<Order> pending = orders.Where(o => o.IsPending); // not evaluated yet
orders.Add(new Order(IsPending: true));
int count = pending.Count();                                  // includes the new order
```

**Async propagation.** Never block with `.Result`/`.Wait()`/`.GetAwaiter().GetResult()` — propagate `await`. No new `async void` outside event handlers. Don't elide `async`/`await` inside `using` or `try`: the resource is disposed before the task completes — this fails on truly async providers (Npgsql) yet can pass in SQLite-backed tests, which complete synchronously:

```csharp
// BROKEN after "simplifying": db is disposed while the query may still be running
Task<List<Order>> LoadAsync() { using var db = factory.CreateDbContext(); return db.Orders.ToListAsync(); }
// Keep the await
async Task<List<Order>> LoadAsync() { using var db = factory.CreateDbContext(); return await db.Orders.ToListAsync(); }
```

**Exceptions.** Rethrow with `throw;` (`throw ex;` resets the stack trace). Keep exception types — callers catch them. Validation moved into an iterator or `async` method throws later (first enumeration / awaited task).

**class → record.** Equality becomes value-based (`==`, dictionary/set keys, `Distinct()`) except collection members, which compare by reference; `ToString()` (often logged) changes. Don't convert EF Core entities — value equality breaks user-initialized `HashSet` navigations and identity-based tracking (mutating a tracked record changes its hash).

**Nullable annotations.** Enabling `<Nullable>` or adding `?` changes warnings (build errors under `TreatWarningsAsErrors`), not runtime behavior. Adding `ThrowIfNull` or `?? throw` does.

**Switch statement → switch expression.** An unmatched statement does nothing; an unmatched expression throws `SwitchExpressionException` (compiler warning CS8509/CS8524). Add a `_ =>` arm reproducing the old fallback.

**EF Core translation.** A query lambda extracted into a plain C# method is untranslatable — EF Core 3+ throws at runtime, and "fixing" it with `AsEnumerable()` loads the whole table. Reuse predicates as `Expression<Func<T, bool>>`. An `IQueryable<T>` → `IEnumerable<T>` parameter silently moves filtering into memory, where C# string rules replace database collation. Compare `query.ToQueryString()` (EF Core 5+) before and after.

```csharp
static readonly Expression<Func<Order, bool>> IsOverdue = o => o.DueDate < DateTime.UtcNow && !o.Paid;
// db: AppDbContext, ct: CancellationToken
var overdue = await db.Orders.Where(IsOverdue).ToListAsync(ct);
```

**DI lifetimes.** A singleton must not depend on scoped services (captive `DbContext`). Moving to `Singleton` shares state across requests; moving `new Foo()` into DI changes who disposes it. The default host validates scopes in Development — start the app there after changing registrations.

**Config → `IOptions<T>`.** A missing key leaves the property at its initializer where `config["X"]` returned `null` — keep the old fallback. `ValidateOnStart()` is a behavior change (startup can fail).

## C# patterns

**Guard clauses** — invert each condition exactly (`total > 100m` becomes `if (total <= 100m) return 0m;`) and only over side-effect-free conditions.

**Primitive → value object** — throw the same exception type and message the old check threw:

```csharp
public readonly record struct Email
{
    public string Value { get; }
    public Email(string value)
    {
        if (!value.Contains('@')) throw new ArgumentException($"Invalid email: {value}", nameof(value));
        Value = value;
    }
}
```

`default(Email)` skips the constructor (`Value` is `null`); use a `sealed record` class if that matters.

## Anti-patterns

- Big-bang rewrites when asked to "refactor".
- Deleting "dead" code without checking reflection, DI assembly scanning, controller routing, and serializers.
- Imposing patterns the codebase doesn't use (MediatR, repositories over `DbContext`, new folder schemes) — ask first.
