using Todo.Domain.Common;

namespace Todo.Domain.Todos;

public sealed record TodoChanges(
    PatchField<string?> Title,
    PatchField<string?> Description,
    PatchField<DateOnly?> DueDate,
    PatchField<TodoPriority?> Priority)
{
    public bool IsEmpty => !Title.HasValue && !Description.HasValue && !DueDate.HasValue && !Priority.HasValue;
}
