using System.Net;
using System.Net.Http.Json;
using System.Text;
using System.Text.Json;
using Todo.IntegrationTests.Fixtures;

namespace Todo.IntegrationTests.Api;

public abstract class TodoApiContract : IAsyncLifetime
{
    private readonly string _owner = $"user-{Guid.NewGuid():N}";
    private TodoApiFactory _factory = null!;
    private HttpClient _client = null!;

    private static CancellationToken Ct => TestContext.Current.CancellationToken;

    private protected abstract TodoApiFactory CreateFactory();

    public ValueTask InitializeAsync()
    {
        _factory = CreateFactory();
        _client = _factory.CreateClient();
        return ValueTask.CompletedTask;
    }

    public async ValueTask DisposeAsync()
    {
        _client.Dispose();
        await _factory.DisposeAsync();
        GC.SuppressFinalize(this);
    }

    private Task<HttpResponseMessage> SendAsync(
        HttpMethod method,
        string url,
        object? body = null,
        string? ifMatch = null,
        string? asUser = null)
    {
        var request = new HttpRequestMessage(method, url);
        if (body is not null)
        {
            request.Content = new StringContent(body as string ?? JsonSerializer.Serialize(body), Encoding.UTF8, "application/json");
        }

        if (ifMatch is not null)
        {
            request.Headers.TryAddWithoutValidation("If-Match", ifMatch);
        }

        if (asUser is not "")
        {
            request.Headers.Add(TestAuthHandler.UserHeader, asUser ?? _owner);
        }

        return _client.SendAsync(request, Ct);
    }

    private async Task<string> CreateAsync(object body)
    {
        var response = await SendAsync(HttpMethod.Post, "/todos", body);
        Assert.Equal(HttpStatusCode.Created, response.StatusCode);
        return response.Headers.Location!.OriginalString;
    }

    private static Task<JsonElement> JsonAsync(HttpResponseMessage response) =>
        response.Content.ReadFromJsonAsync<JsonElement>(Ct);

    private static async Task<string?> ProblemCodeAsync(HttpResponseMessage response)
    {
        Assert.Equal("application/problem+json", response.Content.Headers.ContentType?.MediaType);
        var problem = await JsonAsync(response);
        return problem.TryGetProperty("code", out var code) ? code.GetString() : null;
    }

    [Fact]
    public async Task Post_ValidTodo_Returns201WithLocationAndETag()
    {
        var response = await SendAsync(HttpMethod.Post, "/todos", new { title = "Buy milk", priority = "high" });

        Assert.Equal(HttpStatusCode.Created, response.StatusCode);
        var todo = await JsonAsync(response);
        Assert.Equal($"/todos/{todo.GetProperty("id").GetString()}", response.Headers.Location?.OriginalString);
        Assert.Equal("\"1\"", response.Headers.ETag?.Tag);
        Assert.Equal("high", todo.GetProperty("priority").GetString());
    }

    [Theory]
    [InlineData("""{"title":"x","dueDate":"2026-02-30"}""")]
    [InlineData("""{"title":"x","priority":"urgent"}""")]
    [InlineData("""{"title":"x","priority":1}""")]
    [InlineData("""{"title":"x","priority":"medium,high"}""")]
    [InlineData("""{"title":"x","priority":"High"}""")]
    [InlineData("""{"title":123}""")]
    [InlineData("""{"title":"x","status":"done"}""")]
    [InlineData("""{"title":"a","title":"b"}""")]
    [InlineData("""{bad json""")]
    public async Task Post_InvalidBody_Returns400WithStableCode(string body)
    {
        var response = await SendAsync(HttpMethod.Post, "/todos", body);

        Assert.Equal(HttpStatusCode.BadRequest, response.StatusCode);
        Assert.Equal("VALIDATION_FAILED", await ProblemCodeAsync(response));
    }

    [Fact]
    public async Task Post_BlankTitle_Returns400WithFieldError()
    {
        var response = await SendAsync(HttpMethod.Post, "/todos", new { title = "  " });

        var problem = await JsonAsync(response);
        Assert.Equal(HttpStatusCode.BadRequest, response.StatusCode);
        Assert.True(problem.GetProperty("errors").TryGetProperty("title", out _));
    }

    [Fact]
    public async Task AnyTodoEndpoint_WithoutUser_Returns401()
    {
        var response = await SendAsync(HttpMethod.Get, "/todos", asUser: "");

        Assert.Equal(HttpStatusCode.Unauthorized, response.StatusCode);
    }

    [Fact]
    public async Task AnyTodoEndpoint_WithTokenMissingSubject_Returns403()
    {
        var response = await SendAsync(HttpMethod.Get, "/todos", asUser: TestAuthHandler.WithoutSubject);

        Assert.Equal(HttpStatusCode.Forbidden, response.StatusCode);
    }

    [Fact]
    public async Task Get_AnotherUsersTodo_Returns404()
    {
        var url = await CreateAsync(new { title = "Private" });

        var response = await SendAsync(HttpMethod.Get, url, asUser: "someone-else");

        Assert.Equal(HttpStatusCode.NotFound, response.StatusCode);
        Assert.Equal("TODO_NOT_FOUND", await ProblemCodeAsync(response));
    }

    [Fact]
    public async Task List_FiltersSearchesAndSortsByDueDateWithNullsLast()
    {
        await CreateAsync(new { title = "Milk later", dueDate = "2026-03-01" });
        await CreateAsync(new { title = "MILK soon", dueDate = "2026-02-01" });
        await CreateAsync(new { title = "Milk someday" });
        await CreateAsync(new { title = "Bread 100%" });

        var page = await JsonAsync(await SendAsync(HttpMethod.Get, "/todos?status=open&q=milk&sort=dueDate&limit=10"));

        Assert.Equal(3, page.GetProperty("total").GetInt32());
        Assert.Equal(
            ["MILK soon", "Milk later", "Milk someday"],
            page.GetProperty("items").EnumerateArray().Select(item => item.GetProperty("title").GetString()));
    }

    [Fact]
    public async Task List_SearchTreatsWildcardsLiterally()
    {
        await CreateAsync(new { title = "Bread 100%" });
        await CreateAsync(new { title = "Butter" });

        var page = await JsonAsync(await SendAsync(HttpMethod.Get, "/todos?q=%25"));

        Assert.Equal("Bread 100%", Assert.Single(page.GetProperty("items").EnumerateArray()).GetProperty("title").GetString());
    }

    [Theory]
    [InlineData("/todos?limit=1000")]
    [InlineData("/todos?limit=abc")]
    [InlineData("/todos?status=archived")]
    [InlineData("/todos?status=1")]
    [InlineData("/todos?sort=title")]
    public async Task List_InvalidQuery_Returns400(string url)
    {
        var response = await SendAsync(HttpMethod.Get, url);

        Assert.Equal(HttpStatusCode.BadRequest, response.StatusCode);
        Assert.NotNull(await ProblemCodeAsync(response));
    }

    [Theory]
    [InlineData(null, HttpStatusCode.PreconditionRequired)]
    [InlineData("*", HttpStatusCode.PreconditionRequired)]
    [InlineData("W/\"1\"", HttpStatusCode.PreconditionFailed)]
    [InlineData("1", HttpStatusCode.BadRequest)]
    public async Task Patch_WithUnusableIfMatch_IsRejected(string? ifMatch, HttpStatusCode expected)
    {
        var url = await CreateAsync(new { title = "Buy milk" });

        var response = await SendAsync(HttpMethod.Patch, url, new { title = "x" }, ifMatch);

        Assert.Equal(expected, response.StatusCode);
    }

    [Fact]
    public async Task Patch_WithInvalidEnum_ReportsTheField()
    {
        var url = await CreateAsync(new { title = "Buy milk" });

        var response = await SendAsync(HttpMethod.Patch, url, """{"priority":"medium,high"}""", "\"1\"");

        Assert.Equal(HttpStatusCode.BadRequest, response.StatusCode);
        Assert.True((await JsonAsync(response)).GetProperty("errors").TryGetProperty("priority", out _));
    }

    [Fact]
    public async Task Patch_WithoutIfMatch_Returns428WithType()
    {
        var url = await CreateAsync(new { title = "Buy milk" });

        var response = await SendAsync(HttpMethod.Patch, url, new { title = "x" });

        Assert.Equal(HttpStatusCode.PreconditionRequired, response.StatusCode);
        Assert.Contains("rfc6585", (await JsonAsync(response)).GetProperty("type").GetString(), StringComparison.Ordinal);
    }

    [Fact]
    public async Task Patch_WithStaleETag_Returns412WithCurrentVersion()
    {
        var url = await CreateAsync(new { title = "Buy milk" });
        await SendAsync(HttpMethod.Patch, url, new { title = "First" }, "\"1\"");

        var response = await SendAsync(HttpMethod.Patch, url, new { title = "Second" }, "\"1\"");

        Assert.Equal(HttpStatusCode.PreconditionFailed, response.StatusCode);
        Assert.Equal(2, (await JsonAsync(response)).GetProperty("currentVersion").GetInt32());
    }

    [Fact]
    public async Task Patch_TenConcurrentWritersWithSameETag_ExactlyOneWins()
    {
        var url = await CreateAsync(new { title = "Buy milk" });

        var responses = await Task.WhenAll(Enumerable.Range(0, 10)
            .Select(i => SendAsync(HttpMethod.Patch, url, new { title = $"Writer {i}" }, "\"1\"")));

        Assert.Single(responses, response => response.StatusCode == HttpStatusCode.OK);
        Assert.All(
            responses.Where(response => response.StatusCode != HttpStatusCode.OK),
            response => Assert.Equal(HttpStatusCode.PreconditionFailed, response.StatusCode));
    }

    [Fact]
    public async Task Patch_NullDescription_ClearsOnlyThatField()
    {
        var url = await CreateAsync(new { title = "Buy milk", description = "2 litres" });

        var todo = await JsonAsync(await SendAsync(HttpMethod.Patch, url, """{"description":null}""", "\"1\""));

        Assert.Equal(JsonValueKind.Null, todo.GetProperty("description").ValueKind);
        Assert.Equal("Buy milk", todo.GetProperty("title").GetString());
    }

    [Fact]
    public async Task Complete_Twice_SecondCallIsNoOp()
    {
        var url = await CreateAsync(new { title = "Buy milk" });

        var first = await SendAsync(HttpMethod.Post, $"{url}/complete", ifMatch: "\"1\"");
        var repeat = await SendAsync(HttpMethod.Post, $"{url}/complete", ifMatch: "\"2\"");

        Assert.Equal("done", (await JsonAsync(first)).GetProperty("status").GetString());
        Assert.Equal(HttpStatusCode.OK, repeat.StatusCode);
        Assert.Equal("\"2\"", repeat.Headers.ETag?.Tag);
    }

    [Fact]
    public async Task Delete_WithCurrentVersion_Returns204ThenGetReturns404()
    {
        var url = await CreateAsync(new { title = "Buy milk" });

        var deleted = await SendAsync(HttpMethod.Delete, url, ifMatch: "\"1\"");
        var after = await SendAsync(HttpMethod.Get, url);

        Assert.Equal(HttpStatusCode.NoContent, deleted.StatusCode);
        Assert.Equal(HttpStatusCode.NotFound, after.StatusCode);
    }

    [Fact]
    public async Task UnknownRoute_Returns404ProblemWithCode()
    {
        var response = await SendAsync(HttpMethod.Get, "/nope");

        Assert.Equal(HttpStatusCode.NotFound, response.StatusCode);
        Assert.Equal("NOT_FOUND", await ProblemCodeAsync(response));
    }

    [Fact]
    public async Task Liveness_IsAnonymous()
    {
        var response = await SendAsync(HttpMethod.Get, "/health/live", asUser: "");

        Assert.Equal(HttpStatusCode.OK, response.StatusCode);
    }
}
