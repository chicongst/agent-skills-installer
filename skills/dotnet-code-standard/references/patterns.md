# .NET Patterns — before / after

Code targets .NET 10 / C# 14 and compiles under the reference solution's analyzer settings.

## 1. Outbound HTTP: typed client + resilience (rule 20)

```csharp
// ❌ Socket exhaustion, no timeout, no retry, exception text leaks to callers
var json = await new HttpClient().GetStringAsync($"https://partner/api/sites/{id}");
```

```csharp
// ✅ Program / AddInfrastructure
services.AddHttpClient<PartnerClient>(client => client.BaseAddress = new Uri(options.BaseUrl))
    .AddStandardResilienceHandler();

internal sealed partial class PartnerClient(HttpClient http, ILogger<PartnerClient> logger)
{
    public async Task<Result<PartnerSite>> GetSiteAsync(string siteId, CancellationToken cancellationToken)
    {
        using var response = await http.GetAsync($"sites/{Uri.EscapeDataString(siteId)}", cancellationToken);
        if (response.StatusCode == HttpStatusCode.NotFound)
        {
            return new DomainError(ErrorKind.NotFound, "PARTNER_SITE_NOT_FOUND", $"Site {siteId} not found.");
        }

        if (!response.IsSuccessStatusCode)
        {
            LogUpstreamFailure((int)response.StatusCode, siteId);
            return new DomainError(ErrorKind.Upstream, "UPSTREAM_FAILED", "Partner API is unavailable.");
        }

        var site = await response.Content.ReadFromJsonAsync<PartnerSite>(cancellationToken);
        return site is null ? new DomainError(ErrorKind.Upstream, "UPSTREAM_EMPTY", "Partner API returned no body.") : site;
    }

    [LoggerMessage(Level = LogLevel.Warning, Message = "Partner API returned {StatusCode} for site {SiteId}")]
    private partial void LogUpstreamFailure(int statusCode, string siteId);
}
```

Add `Upstream` to `ErrorKind` and map it to 502 in `Problems`. Use `Microsoft.Extensions.Http.Resilience`, not a direct `Polly` reference (Polly's next major has a maintenance fee for direct users).

## 2. EF Core reads and writes (rules 15, 16, 18)

```csharp
// ❌ Tracks entities it never saves, loads every column, N+1 on Sites, last-write-wins update
var customers = await db.Customers.ToListAsync();
foreach (var c in customers) { c.SiteCount = c.Sites.Count; }
var todo = await db.Todos.FindAsync(id);
todo.Title = request.Title;
await db.SaveChangesAsync();
```

```csharp
// ✅ Projection for reads, one round trip, bounded, owner-scoped
var page = await db.Customers
    .AsNoTracking()
    .Where(c => c.OwnerId == ownerId)
    .OrderBy(c => c.Name).ThenBy(c => c.Id)
    .Select(c => new CustomerSummary(c.Id, c.Name, c.Sites.Count))
    .Skip(offset).Take(limit)
    .ToListAsync(cancellationToken);

// ✅ Full-entity write guarded by the concurrency token — every mapped column is written,
//    the WHERE clause is `id = @id AND version = @expected`, no hand-written column list
var entry = db.Todos.Attach(next);
entry.State = EntityState.Modified;
entry.Property(t => t.OwnerId).IsModified = false;
entry.Property(t => t.Version).OriginalValue = expectedVersion;
try
{
    await db.SaveChangesAsync(cancellationToken);
    return WriteResult.Written;
}
catch (DbUpdateConcurrencyException)
{
    var current = await db.Todos.Where(t => t.Id == next.Id && t.OwnerId == next.OwnerId)
        .Select(t => (int?)t.Version).SingleOrDefaultAsync(cancellationToken);
    return current is { } version ? WriteResult.Mismatch(version) : WriteResult.NotFound;
}
finally
{
    entry.State = EntityState.Detached;
}
```

- `ExecuteUpdateAsync` is for set-based or deliberately partial updates (`UPDATE … SET status = 'archived' WHERE due_date < @cutoff`), not for replacing an aggregate — a forgotten `SetProperty` silently drops a column.
- Several aggregates that must change together: load tracked, mutate, one `SaveChangesAsync` (one transaction). Across contexts or raw SQL: `await using var tx = await db.Database.BeginTransactionAsync(ct)`.
- `CountAsync` then `ToListAsync` on the same context: sequential awaits, never `Task.WhenAll`.
- Map Postgres unique violations (`PostgresException { SqlState: PostgresErrorCodes.UniqueViolation }`) to a domain error inside the repository.

### Keyset pagination for large or partner-facing lists

```csharp
// cursor = base64("{createdAt:O}|{id}") of the last item on the previous page
var items = await db.Todos.AsNoTracking()
    .Where(t => t.OwnerId == ownerId)
    .Where(t => t.CreatedAt < after.CreatedAt || (t.CreatedAt == after.CreatedAt && t.Id.CompareTo(after.Id) < 0))
    .OrderByDescending(t => t.CreatedAt).ThenByDescending(t => t.Id)
    .Take(limit + 1)
    .ToListAsync(cancellationToken);
var nextCursor = items.Count > limit ? Cursor.Encode(items[limit - 1]) : null;
```

Back it with an index on `(owner_id, created_at DESC, id DESC)`.

## 3. Background work: `BackgroundService` with scopes and cancellation (rules 7, 20)

```csharp
internal sealed partial class OutboxPublisher(
    IServiceScopeFactory scopes,
    TimeProvider time,
    ILogger<OutboxPublisher> logger) : BackgroundService
{
    private static readonly TimeSpan Interval = TimeSpan.FromSeconds(5);

    protected override async Task ExecuteAsync(CancellationToken stoppingToken)
    {
        using var timer = new PeriodicTimer(Interval, time);
        while (await timer.WaitForNextTickAsync(stoppingToken))
        {
            try
            {
                await using var scope = scopes.CreateAsyncScope();
                var publisher = scope.ServiceProvider.GetRequiredService<PublishPendingMessagesHandler>();
                await publisher.HandleAsync(batchSize: 100, stoppingToken);
            }
            catch (Exception ex) when (ex is not OperationCanceledException)
            {
                LogBatchFailed(ex);
            }
        }
    }

    [LoggerMessage(Level = LogLevel.Error, Message = "Outbox batch failed; retrying on next tick")]
    private partial void LogBatchFailed(Exception exception);
}
```

A hosted service is a singleton: never inject a `DbContext` or scoped handler into it directly — create a scope per unit of work. Every message handler must be idempotent (processed-message table with a unique key).

## 4. Options that fail at boot (rule 21)

```csharp
public sealed class PartnerOptions
{
    public const string SectionName = "Partner";

    [Required, Url]
    public required string BaseUrl { get; init; }

    [Range(1, 60)]
    public int TimeoutSeconds { get; init; } = 10;
}

services.AddOptions<PartnerOptions>()
    .BindConfiguration(PartnerOptions.SectionName)
    .ValidateDataAnnotations()
    .ValidateOnStart();
```

Cross-field rules: implement `IValidatableObject` (see `StorageOptions`) or `IValidateOptions<T>`.

Framework options are validated the same way. JWT: fail at boot when neither an Authority nor signing keys are configured (`dotnet user-jwts` supplies signing keys in Development, so local runs still work):

```csharp
services.AddAuthentication(JwtBearerDefaults.AuthenticationScheme).AddJwtBearer();
services.AddOptions<JwtBearerOptions>(JwtBearerDefaults.AuthenticationScheme)
    .Validate(
        options => !string.IsNullOrWhiteSpace(options.Authority)
            || options.TokenValidationParameters.IssuerSigningKeys?.Any() == true,
        "Authentication:Schemes:Bearer:Authority is required.")
    .ValidateOnStart();
```

Integration tests set `Authentication:Schemes:Bearer:Authority` to a dummy URL with `UseSetting` and replace the scheme with a test handler; the dummy is never contacted.

## 5. Minimal API pitfalls

| Pitfall | Symptom | Fix |
|---|---|---|
| Enum parameter binding uses `Enum.TryParse` | `?status=1` binds to `Done` | Bind `string?`, map through an explicit dictionary |
| Default STJ ignores unknown JSON members | `{"title":"x","isAdmin":true}` accepted | `UnmappedMemberHandling.Disallow` |
| Default enum converter accepts numbers | `"priority": 2` accepted | `JsonStringEnumConverter(JsonNamingPolicy.CamelCase, allowIntegerValues: false)` |
| `ThrowOnBadRequest` is false outside Development | Bad JSON → empty 400 in production, detailed in dev | Set it to `true`; handle `BadHttpRequestException` in `IExceptionHandler` |
| No `UseStatusCodePages` | Unknown route → empty 404 body | `AddProblemDetails()` + `UseStatusCodePages()` |
| Route constraint `{id:guid}` | Malformed id → 404, not 400 | Accept it (documented) or bind `string` and validate |
| Returning `IResult` | OpenAPI can't describe responses | `Task<Results<Ok<T>, ProblemHttpResult>>` with `TypedResults` |
| `[FromBody]` record with `string Title` (non-nullable) | Missing field → `null` slips past nullability | Accept `string?` in the contract and validate in the domain |
| `JsonStringEnumConverter` | Accepts `"medium,high"` (flags) and `"HIGH"`; an undefined value is stored and every later serialization throws → list endpoint 500 for everyone | Strict converter over an exact-name dictionary + `Enum.IsDefined` in the domain |
| Duplicate JSON keys | `{"title":"a","title":"b"}` silently takes the last | `AllowDuplicateProperties = false` |
| `RequireAuthorization()` on a group | Uses the default policy; requirements added only to the fallback policy never run there (a token without `sub` → 500) | Build one policy, `SetDefaultPolicy` + `SetFallbackPolicy` |
| Fallback auth policy | Unknown routes return 401 to anonymous callers, 404 only when authenticated | Expected; document it in the HTTP contract |
| `dotnet run` with `launchSettings.json` | `ASPNETCORE_ENVIRONMENT=Production` is overridden to Development | `--no-launch-profile` when testing environment-specific behaviour |
| `WebApplicationFactory` + `ConfigureAppConfiguration` | Values read in `Program.cs` before `Build()` don't see the override | `builder.UseSetting(key, value)` in `ConfigureWebHost` |
| Kestrel `MaxRequestBodySize` | TestServer ignores it, so no integration test sees 413 | Kestrel smoke test, or `IHttpMaxRequestBodySizeFeature` in middleware |

## 6. Domain modelling choices

| Situation | Choose |
|---|---|
| Aggregate with invariants, replaced whole on save | Immutable `sealed record` with `private init` + `with` inside methods (the reference). Never rely on record value equality for an entity; compare `Version` to detect "no change" |
| Aggregate with child collections tracked by EF | `sealed class` with private setters, private `List<T>` field exposed as `IReadOnlyList<T>`, methods that mutate and raise domain events |
| Value with rules (email, postcode) | `readonly record struct` with `static Result<T> Create(string)` |
| Identifier shared across services | Typed ID `readonly record struct CustomerId(Guid Value)` once there are two or more ID types to confuse |

## 7. Controllers projects (when the solution already uses MVC)

Keep the same Domain / Application / Infrastructure projects. Controllers are thin: `[ApiController]`, one action calls one handler, return `ActionResult<TResponse>`; map `Result<T>` with one `ToActionResult()` extension; keep `AddProblemDetails` + `IExceptionHandler`. Do not mix controllers and minimal APIs for the same resource.

## 8. Logging

```csharp
// ❌ String interpolation: allocates on every call, loses structure, can log PII
_logger.LogInformation($"Customer {customer.Email} created todo {todo.Id}");
```

```csharp
// ✅
[LoggerMessage(Level = LogLevel.Information, Message = "Todo {TodoId} created for customer {CustomerId}")]
private partial void LogCreated(Guid todoId, Guid customerId);
```

Use scopes for request-wide context (`using var _ = logger.BeginScope(new Dictionary<string, object> { ["TenantId"] = tenantId })`); OpenTelemetry carries the trace id automatically.

## 9. Choosing packages (licences checked 2026-10-26)

| Need | Default | Avoid / note |
|---|---|---|
| Mediator | Direct handlers; `Mediator` (MIT, source-generated) if a pipeline is truly needed | MediatR 13+ — RPL-1.5 or commercial licence key |
| Mapping | Hand-written `From(...)` / extension methods | AutoMapper 15+ — commercial licence |
| Validation | Domain `Create` + strict JSON; .NET 10 `AddValidation()` for DataAnnotations on contracts; FluentValidation (Apache-2.0) for complex rules | — |
| Assertions | xUnit `Assert`, or Shouldly | FluentAssertions 8+ — paid for commercial use |
| Mocks | Fakes you write; NSubstitute when needed | Moq (SponsorLink history) |
| Resilience | `Microsoft.Extensions.Http.Resilience` | Direct `Polly` next major — maintenance fee |
| Messaging | Wolverine / MassTransit v8 (Apache-2.0) | MassTransit v9 — commercial |
| Data | EF Core + provider; Dapper for hot read paths | Generic repository over EF; `EF InMemory` for tests |
| API docs | `Microsoft.AspNetCore.OpenApi` (+ Scalar UI) | Swashbuckle for new projects |
| Logging | `ILogger` + OpenTelemetry | Serilog is optional, only for its sinks |

## 10. Idempotent create (rule 9)

```csharp
// Endpoint: header is optional; when present, a retry returns the first result instead of a duplicate
private static async Task<Results<Created<TodoResponse>, Ok<TodoResponse>, ProblemHttpResult>> CreateAsync(
    CreateTodoRequest request,
    [FromHeader(Name = "Idempotency-Key")] string? idempotencyKey,
    ClaimsPrincipal user,
    CreateTodoHandler handler,
    CancellationToken cancellationToken)
```

Store `(owner_id, idempotency_key) → (request_hash, todo_id)` with a unique constraint and a TTL (24 h). Same key + same body hash → return the stored todo with 200; same key + different body → 422 `IDEMPOTENCY_KEY_REUSED`. Insert the key and the todo in one transaction.

## 11. Analyzer pitfalls (latest-recommended + warnings as errors)

| Rule | Trigger | Fix |
|---|---|---|
| CA1716 | Type named `Error`, `Optional`, `Next`… (VB keywords) | `DomainError`, `PatchField<T>` |
| CA1000 | Static factory on a generic type (`Result<T>.Success`) | Non-generic `Result.Success<T>(value)` helper + implicit conversions |
| CA1515 | Public types in an exe project | `internal` (WebApplicationFactory still sees the generated `Program`) |
| CA1848 | `logger.LogInformation(...)` | `[LoggerMessage]` partial methods |
| CA1707 | Underscores in test names | `.editorconfig` `[tests/**.cs] dotnet_diagnostic.CA1707.severity = none` |
| IDE0005 not enforced | `GenerateDocumentationFile` off | Turn it on; suppress only CS1591 |
| CA1861 / IDE0161 in migrations | EF-generated code | `[src/**/Migrations/*.cs] generated_code = true` |
| CS0108 in auth handler tests | `const string Scheme` hides `AuthenticationHandler.Scheme` | Name it `SchemeName` |

## 12. In-memory now, database later

When the task explicitly allows in-memory storage, keep everything that makes the swap cheap and skip only what has nothing to act on:

| Keep | Skip until a database exists |
|---|---|
| `ITodoRepository` port, `internal` in-memory implementation behind a `Lock` | EF Core, migrations, Testcontainers |
| Four projects only if rule 2 holds today; otherwise one Api project with `Storage/` and `Todos/` folders | `compose.yaml` |
| `Storage:Driver` option with **no default**, `Memory` only in Development settings | Readiness checks (still map `/health/ready`, with no checks) |
| The HTTP contract as an abstract test class, so the database backend plugs into the same tests | `dotnet-ef` in the tool manifest |
| Version + If-Match concurrency in the repository contract (`WriteResult` with current version) | — |
| An ADR stating what the database step adds | — |
