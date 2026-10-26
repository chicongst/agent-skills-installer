using System.Text.Json;
using Microsoft.AspNetCore.Diagnostics;
using Microsoft.AspNetCore.Mvc;

namespace Todo.Api.Http;

internal sealed partial class GlobalExceptionHandler(
    IProblemDetailsService problemDetails,
    ILogger<GlobalExceptionHandler> logger) : IExceptionHandler
{
    public async ValueTask<bool> TryHandleAsync(
        HttpContext httpContext,
        Exception exception,
        CancellationToken cancellationToken)
    {
        var problem = exception switch
        {
            BadHttpRequestException { InnerException: JsonException json } => InvalidJson(json),
            BadHttpRequestException bad => new ProblemDetails
            {
                Status = bad.StatusCode,
                Title = "Bad request",
                Detail = "A route, query or header value has an invalid format.",
            },
            OperationCanceledException when httpContext.RequestAborted.IsCancellationRequested => new ProblemDetails
            {
                Status = StatusCodes.Status499ClientClosedRequest,
                Title = "Client closed request",
            },
            _ => new ProblemDetails { Status = StatusCodes.Status500InternalServerError, Title = "Internal server error" },
        };

        if (problem.Status >= StatusCodes.Status500InternalServerError)
        {
            LogUnhandled(exception, httpContext.Request.Method, httpContext.Request.Path);
        }

        httpContext.Response.StatusCode = problem.Status ?? StatusCodes.Status500InternalServerError;
        return await problemDetails.TryWriteAsync(new ProblemDetailsContext
        {
            HttpContext = httpContext,
            Exception = exception,
            ProblemDetails = problem,
        });
    }

    private static ProblemDetails InvalidJson(JsonException json)
    {
        var field = string.IsNullOrEmpty(json.Path) || json.Path == "$" ? "body" : json.Path.TrimStart('$', '.');
        return new ProblemDetails
        {
            Status = StatusCodes.Status400BadRequest,
            Title = "Validation failed",
            Detail = "The request body is not valid JSON for this endpoint.",
            Extensions =
            {
                ["code"] = "VALIDATION_FAILED",
                ["errors"] = new Dictionary<string, string[]> { [field] = ["Invalid or unexpected value."] },
            },
        };
    }

    [LoggerMessage(Level = LogLevel.Error, Message = "Unhandled exception for {Method} {Path}")]
    private partial void LogUnhandled(Exception exception, string method, PathString path);
}
