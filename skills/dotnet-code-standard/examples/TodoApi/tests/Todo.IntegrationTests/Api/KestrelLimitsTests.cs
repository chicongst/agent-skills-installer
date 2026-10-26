using System.Net;
using System.Net.Http.Json;
using System.Text;
using System.Text.Json;
using Todo.IntegrationTests.Fixtures;

namespace Todo.IntegrationTests.Api;

public sealed class KestrelLimitsTests
{
    [Fact]
    public async Task Post_BodyOverOneMegabyte_Returns413ProblemWithCode()
    {
        var ct = TestContext.Current.CancellationToken;
        await using var factory = TodoApiFactory.InMemory();
        factory.UseKestrel(0);
        factory.StartServer();
        using var client = factory.CreateClient();
        using var request = new HttpRequestMessage(HttpMethod.Post, "/todos")
        {
            Content = new StringContent(
                $$"""{"title":"x","description":"{{new string('a', 1_100_000)}}"}""",
                Encoding.UTF8,
                "application/json"),
        };
        request.Headers.Add(TestAuthHandler.UserHeader, "user-kestrel");

        using var response = await client.SendAsync(request, ct);

        Assert.Equal(HttpStatusCode.RequestEntityTooLarge, response.StatusCode);
        var problem = await response.Content.ReadFromJsonAsync<JsonElement>(ct);
        Assert.Equal("PAYLOAD_TOO_LARGE", problem.GetProperty("code").GetString());
    }
}
