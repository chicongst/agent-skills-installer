using Microsoft.AspNetCore.Http.HttpResults;
using Todo.Domain.Common;

namespace Todo.Api.Http;

internal static class Problems
{
    public static ProblemHttpResult From(DomainError error)
    {
        ArgumentNullException.ThrowIfNull(error);

        var extensions = new Dictionary<string, object?> { ["code"] = error.Code };
        if (error.Field is not null)
        {
            extensions["errors"] = new Dictionary<string, string[]> { [error.Field] = [error.Message] };
        }

        foreach (var (key, value) in error.Details ?? new Dictionary<string, object?>())
        {
            extensions[key] = value;
        }

        var (status, title) = error.Kind switch
        {
            ErrorKind.Validation => (StatusCodes.Status400BadRequest, "Validation failed"),
            ErrorKind.NotFound => (StatusCodes.Status404NotFound, "Not found"),
            ErrorKind.VersionMismatch => (StatusCodes.Status412PreconditionFailed, "Version mismatch"),
            _ => throw new ArgumentOutOfRangeException(nameof(error), error.Kind, "Unmapped error kind."),
        };

        return TypedResults.Problem(statusCode: status, title: title, detail: error.Message, extensions: extensions);
    }

    public static ProblemHttpResult For(IfMatch ifMatch) => ifMatch.State switch
    {
        IfMatchState.Missing => PreconditionRequired("Send If-Match with the ETag from your last read."),
        IfMatchState.Wildcard => PreconditionRequired("If-Match: * is not accepted; send the specific ETag you read."),
        IfMatchState.Weak => TypedResults.Problem(
            statusCode: StatusCodes.Status412PreconditionFailed,
            title: "Version mismatch",
            detail: "Weak ETags never match If-Match; send the strong ETag from your last read.",
            extensions: new Dictionary<string, object?> { ["code"] = "VERSION_MISMATCH" }),
        _ => From(DomainError.Validation("If-Match", "If-Match must be a strong ETag such as \"3\".")),
    };

    private static ProblemHttpResult PreconditionRequired(string detail) =>
        TypedResults.Problem(
            statusCode: StatusCodes.Status428PreconditionRequired,
            title: "Precondition required",
            detail: detail,
            extensions: new Dictionary<string, object?> { ["code"] = "PRECONDITION_REQUIRED" });
}
