using Microsoft.AspNetCore.Diagnostics.HealthChecks;
using Todo.Infrastructure;

namespace Todo.Api.Health;

internal static class HealthEndpoints
{
    public static IEndpointRouteBuilder MapHealthEndpoints(this IEndpointRouteBuilder app)
    {
        app.MapHealthChecks("/health/live", new HealthCheckOptions { Predicate = _ => false }).AllowAnonymous();
        app.MapHealthChecks(
            "/health/ready",
            new HealthCheckOptions { Predicate = check => check.Tags.Contains(HealthCheckTags.Ready) })
            .AllowAnonymous();

        return app;
    }
}
