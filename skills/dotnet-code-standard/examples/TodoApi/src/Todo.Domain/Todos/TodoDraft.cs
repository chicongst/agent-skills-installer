namespace Todo.Domain.Todos;

public sealed record TodoDraft(string? Title, string? Description, DateOnly? DueDate, TodoPriority? Priority);
