namespace Todo.Domain.Common;

public sealed record DomainError(
    ErrorKind Kind,
    string Code,
    string Message,
    string? Field = null,
    IReadOnlyDictionary<string, object?>? Details = null)
{
    public static DomainError Validation(string field, string message) =>
        new(ErrorKind.Validation, "VALIDATION_FAILED", message, field);
}
