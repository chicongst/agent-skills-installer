using Microsoft.Extensions.Logging;
using Todo.Application.Abstractions;
using Todo.Domain.Common;
using Todo.Domain.Todos;

namespace Todo.Application.Todos.ReopenTodo;

public sealed record ReopenTodoCommand(string OwnerId, Guid Id, int ExpectedVersion);

public sealed class ReopenTodoHandler(ITodoRepository todos, TimeProvider time, ILogger<ReopenTodoHandler> logger)
{
    public async Task<Result<TodoItem>> HandleAsync(ReopenTodoCommand command, CancellationToken cancellationToken)
    {
        ArgumentNullException.ThrowIfNull(command);

        var current = await VersionedWrite.LoadAsync(
            todos, command.OwnerId, command.Id, command.ExpectedVersion, logger, cancellationToken);
        if (!current.IsSuccess)
        {
            return current;
        }

        var next = current.Value.Reopen(time.GetUtcNow());
        if (next.Version == current.Value.Version)
        {
            return next;
        }

        var written = await todos.UpdateAsync(next, command.ExpectedVersion, cancellationToken);
        return VersionedWrite.ToError(written, command.Id, command.ExpectedVersion, logger) is { } error
            ? error
            : next;
    }
}
