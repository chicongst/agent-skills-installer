using System.Security.Claims;
using System.Text.Json.Serialization;
using Microsoft.AspNetCore.Authentication.JwtBearer;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Http.Json;
using Todo.Api.Auth;
using Todo.Api.Http;

namespace Todo.Api;

internal static class DependencyInjection
{
    private static readonly Dictionary<int, string> CodesByStatus = new()
    {
        [StatusCodes.Status400BadRequest] = "BAD_REQUEST",
        [StatusCodes.Status401Unauthorized] = "UNAUTHORIZED",
        [StatusCodes.Status403Forbidden] = "FORBIDDEN",
        [StatusCodes.Status404NotFound] = "NOT_FOUND",
        [StatusCodes.Status405MethodNotAllowed] = "METHOD_NOT_ALLOWED",
        [StatusCodes.Status413PayloadTooLarge] = "PAYLOAD_TOO_LARGE",
        [StatusCodes.Status415UnsupportedMediaType] = "UNSUPPORTED_MEDIA_TYPE",
        [StatusCodes.Status428PreconditionRequired] = "PRECONDITION_REQUIRED",
        [StatusCodes.Status429TooManyRequests] = "TOO_MANY_REQUESTS",
        [StatusCodes.Status500InternalServerError] = "INTERNAL_ERROR",
    };

    private static readonly Dictionary<int, string> TypesByStatus = new()
    {
        [StatusCodes.Status428PreconditionRequired] = "https://www.rfc-editor.org/rfc/rfc6585#section-3",
        [StatusCodes.Status429TooManyRequests] = "https://www.rfc-editor.org/rfc/rfc6585#section-4",
    };

    public static IServiceCollection AddApi(this IServiceCollection services)
    {
        services.Configure<JsonOptions>(options =>
        {
            var json = options.SerializerOptions;
            json.UnmappedMemberHandling = JsonUnmappedMemberHandling.Disallow;
            json.AllowDuplicateProperties = false;
            json.Converters.Add(new StrictEnumConverterFactory());
            json.Converters.Add(new PatchFieldJsonConverterFactory());
        });
        services.Configure<RouteHandlerOptions>(options => options.ThrowOnBadRequest = true);

        services.AddProblemDetails(options => options.CustomizeProblemDetails = context =>
        {
            var status = context.ProblemDetails.Status ?? context.HttpContext.Response.StatusCode;
            if (!context.ProblemDetails.Extensions.ContainsKey("code") && CodesByStatus.TryGetValue(status, out var code))
            {
                context.ProblemDetails.Extensions["code"] = code;
            }

            if (context.ProblemDetails.Type is null && TypesByStatus.TryGetValue(status, out var type))
            {
                context.ProblemDetails.Type = type;
            }
        });
        services.AddExceptionHandler<GlobalExceptionHandler>();

        services.AddAuthentication(JwtBearerDefaults.AuthenticationScheme).AddJwtBearer();
        services.AddOptions<JwtBearerOptions>(JwtBearerDefaults.AuthenticationScheme)
            .Validate(
                options => !string.IsNullOrWhiteSpace(options.Authority)
                    || options.TokenValidationParameters.IssuerSigningKeys?.Any() == true,
                "Authentication:Schemes:Bearer:Authority is required (in Development run 'dotnet user-jwts create').")
            .ValidateOnStart();
        var signedInUser = new AuthorizationPolicyBuilder()
            .RequireAuthenticatedUser()
            .RequireClaim(ClaimTypes.NameIdentifier)
            .Build();
        services.AddAuthorizationBuilder()
            .SetDefaultPolicy(signedInUser)
            .SetFallbackPolicy(signedInUser);
        services.AddTodoRateLimits();

        services.AddOpenApi();
        return services;
    }
}
