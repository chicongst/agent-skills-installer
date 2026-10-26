using Todo.Domain.Common;

namespace Todo.Domain.Todos;

public sealed record TodoItem
{
    public const int TitleMaxLength = 200;
    public const int DescriptionMaxLength = 5000;
    public const int OwnerIdMaxLength = 128;

    private TodoItem()
    {
    }

    public Guid Id { get; private init; }

    public string OwnerId { get; private init; } = string.Empty;

    public string Title { get; private init; } = string.Empty;

    public string? Description { get; private init; }

    public DateOnly? DueDate { get; private init; }

    public TodoPriority? Priority { get; private init; }

    public TodoStatus Status { get; private init; }

    public DateTimeOffset? CompletedAt { get; private init; }

    public int Version { get; private init; }

    public DateTimeOffset CreatedAt { get; private init; }

    public DateTimeOffset UpdatedAt { get; private init; }

    public static Result<TodoItem> Create(Guid id, string ownerId, TodoDraft draft, DateTimeOffset now)
    {
        ArgumentNullException.ThrowIfNull(draft);

        if (string.IsNullOrWhiteSpace(ownerId) || ownerId.Length > OwnerIdMaxLength)
        {
            return TodoErrors.OwnerRequired;
        }

        var title = ValidateTitle(draft.Title);
        if (!title.IsSuccess)
        {
            return title.Error;
        }

        var description = ValidateDescription(draft.Description);
        if (!description.IsSuccess)
        {
            return description.Error;
        }

        var priority = ValidatePriority(draft.Priority);
        if (!priority.IsSuccess)
        {
            return priority.Error;
        }

        return new TodoItem
        {
            Id = id,
            OwnerId = ownerId,
            Title = title.Value,
            Description = description.Value,
            DueDate = draft.DueDate,
            Priority = priority.Value,
            Status = TodoStatus.Open,
            Version = 1,
            CreatedAt = now,
            UpdatedAt = now,
        };
    }

    public Result<TodoItem> Apply(TodoChanges changes, DateTimeOffset now)
    {
        ArgumentNullException.ThrowIfNull(changes);

        if (changes.IsEmpty)
        {
            return TodoErrors.EmptyChanges;
        }

        var title = changes.Title.HasValue ? ValidateTitle(changes.Title.Value) : Title;
        if (!title.IsSuccess)
        {
            return title.Error;
        }

        var description = changes.Description.HasValue ? ValidateDescription(changes.Description.Value) : Description;
        if (!description.IsSuccess)
        {
            return description.Error;
        }

        var priority = changes.Priority.HasValue ? ValidatePriority(changes.Priority.Value) : Priority;
        if (!priority.IsSuccess)
        {
            return priority.Error;
        }

        return Touch(
            this with
            {
                Title = title.Value,
                Description = description.Value,
                DueDate = changes.DueDate.GetValueOrDefault(DueDate),
                Priority = priority.Value,
            },
            now);
    }

    public TodoItem Complete(DateTimeOffset now) =>
        Status == TodoStatus.Done ? this : Touch(this with { Status = TodoStatus.Done, CompletedAt = now }, now);

    public TodoItem Reopen(DateTimeOffset now) =>
        Status == TodoStatus.Open ? this : Touch(this with { Status = TodoStatus.Open, CompletedAt = null }, now);

    private static TodoItem Touch(TodoItem todo, DateTimeOffset now) =>
        todo with { Version = todo.Version + 1, UpdatedAt = now };

    private static Result<string> ValidateTitle(string? title)
    {
        var trimmed = title?.Trim();
        if (string.IsNullOrEmpty(trimmed))
        {
            return TodoErrors.TitleRequired;
        }

        return trimmed.Length > TitleMaxLength ? TodoErrors.TitleTooLong : trimmed;
    }

    private static Result<string?> ValidateDescription(string? description)
    {
        var trimmed = description?.Trim();
        if (string.IsNullOrEmpty(trimmed))
        {
            return Result.Success<string?>(null);
        }

        return trimmed.Length > DescriptionMaxLength ? TodoErrors.DescriptionTooLong : trimmed;
    }

    private static Result<TodoPriority?> ValidatePriority(TodoPriority? priority) =>
        priority is { } value && !Enum.IsDefined(value) ? TodoErrors.PriorityInvalid : priority;
}
