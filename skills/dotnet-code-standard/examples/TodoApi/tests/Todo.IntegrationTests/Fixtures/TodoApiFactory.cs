using Microsoft.AspNetCore.Authentication;
using Microsoft.AspNetCore.Hosting;
using Microsoft.AspNetCore.Mvc.Testing;
using Microsoft.AspNetCore.TestHost;
using Microsoft.Extensions.DependencyInjection;

namespace Todo.IntegrationTests.Fixtures;

internal sealed class TodoApiFactory(IReadOnlyDictionary<string, string?> settings) : WebApplicationFactory<Program>
{
    public static TodoApiFactory InMemory() => new(new Dictionary<string, string?> { ["Storage:Driver"] = "Memory" });

    public static TodoApiFactory Postgres(string connectionString) => new(new Dictionary<string, string?>
    {
        ["Storage:Driver"] = "Postgres",
        ["Storage:ConnectionString"] = connectionString,
    });

    protected override void ConfigureWebHost(IWebHostBuilder builder)
    {
        builder.UseEnvironment("Testing");
        builder.UseSetting("Authentication:Schemes:Bearer:Authority", "https://login.test.invalid");
        foreach (var (key, value) in settings)
        {
            builder.UseSetting(key, value);
        }

        builder.ConfigureTestServices(services => services
            .AddAuthentication(TestAuthHandler.SchemeName)
            .AddScheme<AuthenticationSchemeOptions, TestAuthHandler>(TestAuthHandler.SchemeName, null));
    }
}
