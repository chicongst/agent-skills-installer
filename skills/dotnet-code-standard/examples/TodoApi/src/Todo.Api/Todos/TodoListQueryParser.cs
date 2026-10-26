using Todo.Application.Abstractions;
using Todo.Domain.Common;
using Todo.Domain.Todos;

namespace Todo.Api.Todos;

internal static class TodoListQueryParser
{
    private const int DefaultLimit = 20;

    private static readonly Dictionary<string, TodoStatus> Statuses = new(StringComparer.Ordinal)
    {
        ["open"] = TodoStatus.Open,
        ["done"] = TodoStatus.Done,
    };

    private static readonly Dictionary<string, TodoSort> Sorts = new(StringComparer.Ordinal)
    {
        ["createdAt"] = new(TodoSortField.CreatedAt, Descending: false),
        ["-createdAt"] = new(TodoSortField.CreatedAt, Descending: true),
        ["dueDate"] = new(TodoSortField.DueDate, Descending: false),
        ["-dueDate"] = new(TodoSortField.DueDate, Descending: true),
    };

    public static Result<TodoListQuery> Parse(string ownerId, ListTodosParameters parameters)
    {
        TodoStatus? status = null;
        if (parameters.Status is not null)
        {
            if (!Statuses.TryGetValue(parameters.Status, out var parsed))
            {
                return DomainError.Validation("status", "Status must be 'open' or 'done'.");
            }

            status = parsed;
        }

        if (!Sorts.TryGetValue(parameters.Sort ?? "-createdAt", out var sort))
        {
            return DomainError.Validation("sort", $"Sort must be one of: {string.Join(", ", Sorts.Keys)}.");
        }

        var page = new PageRequest(parameters.Limit ?? DefaultLimit, parameters.Offset ?? 0);
        return new TodoListQuery(ownerId, status, parameters.Q, sort, page);
    }
}
