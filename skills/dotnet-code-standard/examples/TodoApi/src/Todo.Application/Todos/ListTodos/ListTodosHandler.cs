using Todo.Application.Abstractions;
using Todo.Domain.Common;
using Todo.Domain.Todos;

namespace Todo.Application.Todos.ListTodos;

public sealed class ListTodosHandler(ITodoRepository todos)
{
    private const int MaxSearchLength = 100;

    public async Task<Result<Page<TodoItem>>> HandleAsync(TodoListQuery query, CancellationToken cancellationToken)
    {
        ArgumentNullException.ThrowIfNull(query);

        if (query.Page.Limit is < 1 or > PageRequest.MaxLimit)
        {
            return DomainError.Validation("limit", $"Limit must be between 1 and {PageRequest.MaxLimit}.");
        }

        if (query.Page.Offset is < 0 or > PageRequest.MaxOffset)
        {
            return DomainError.Validation("offset", $"Offset must be between 0 and {PageRequest.MaxOffset}.");
        }

        var search = string.IsNullOrWhiteSpace(query.Search) ? null : query.Search.Trim();
        if (search?.Length > MaxSearchLength)
        {
            return DomainError.Validation("q", $"Search text must be at most {MaxSearchLength} characters.");
        }

        return await todos.ListAsync(query with { Search = search }, cancellationToken);
    }
}
