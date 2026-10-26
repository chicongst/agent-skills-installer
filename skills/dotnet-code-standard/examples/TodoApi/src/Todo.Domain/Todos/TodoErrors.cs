using Todo.Domain.Common;

namespace Todo.Domain.Todos;

public static class TodoErrors
{
    public static readonly DomainError TitleRequired = DomainError.Validation("title", "Title is required.");

    public static readonly DomainError TitleTooLong =
        DomainError.Validation("title", $"Title must be at most {TodoItem.TitleMaxLength} characters.");

    public static readonly DomainError DescriptionTooLong =
        DomainError.Validation("description", $"Description must be at most {TodoItem.DescriptionMaxLength} characters.");

    public static readonly DomainError PriorityInvalid =
        DomainError.Validation("priority", "Priority must be 'low', 'medium' or 'high'.");

    public static readonly DomainError OwnerRequired = DomainError.Validation("ownerId", "Owner is required.");

    public static readonly DomainError EmptyChanges = DomainError.Validation("body", "At least one field must be provided.");

    public static DomainError NotFound(Guid id) =>
        new(ErrorKind.NotFound, "TODO_NOT_FOUND", $"Todo {id} was not found.");

    public static DomainError VersionMismatch(int currentVersion) =>
        new(
            ErrorKind.VersionMismatch,
            "VERSION_MISMATCH",
            "Todo was modified by someone else; reload and retry.",
            Details: new Dictionary<string, object?> { ["currentVersion"] = currentVersion });
}
