using Todo.Application.Abstractions;
using Todo.Domain.Common;
using Todo.Domain.Todos;

namespace Todo.Api.Todos;

internal sealed record CreateTodoRequest(string? Title, string? Description, DateOnly? DueDate, TodoPriority? Priority)
{
    public TodoDraft ToDraft() => new(Title, Description, DueDate, Priority);
}

internal sealed record UpdateTodoRequest(
    PatchField<string?> Title,
    PatchField<string?> Description,
    PatchField<DateOnly?> DueDate,
    PatchField<TodoPriority?> Priority)
{
    public TodoChanges ToChanges() => new(Title, Description, DueDate, Priority);
}

internal sealed record ListTodosParameters(string? Status, string? Q, string? Sort, int? Limit, int? Offset);

internal sealed record TodoResponse(
    Guid Id,
    string Title,
    string? Description,
    DateOnly? DueDate,
    TodoPriority? Priority,
    TodoStatus Status,
    DateTimeOffset? CompletedAt,
    int Version,
    DateTimeOffset CreatedAt,
    DateTimeOffset UpdatedAt)
{
    public static TodoResponse From(TodoItem todo) => new(
        todo.Id,
        todo.Title,
        todo.Description,
        todo.DueDate,
        todo.Priority,
        todo.Status,
        todo.CompletedAt,
        todo.Version,
        todo.CreatedAt,
        todo.UpdatedAt);
}

internal sealed record TodoPageResponse(IReadOnlyList<TodoResponse> Items, int Total, int Limit, int Offset)
{
    public static TodoPageResponse From(Page<TodoItem> page) =>
        new([.. page.Items.Select(TodoResponse.From)], page.Total, page.Limit, page.Offset);
}
