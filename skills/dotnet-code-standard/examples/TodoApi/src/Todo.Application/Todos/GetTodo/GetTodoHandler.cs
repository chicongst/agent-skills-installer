using Todo.Application.Abstractions;
using Todo.Domain.Common;
using Todo.Domain.Todos;

namespace Todo.Application.Todos.GetTodo;

public sealed record GetTodoQuery(string OwnerId, Guid Id);

public sealed class GetTodoHandler(ITodoRepository todos)
{
    public async Task<Result<TodoItem>> HandleAsync(GetTodoQuery query, CancellationToken cancellationToken)
    {
        ArgumentNullException.ThrowIfNull(query);

        var todo = await todos.FindAsync(query.OwnerId, query.Id, cancellationToken);
        return todo is null ? TodoErrors.NotFound(query.Id) : todo;
    }
}
