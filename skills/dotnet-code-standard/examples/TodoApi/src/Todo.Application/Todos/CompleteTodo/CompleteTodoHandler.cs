using Microsoft.Extensions.Logging;
using Todo.Application.Abstractions;
using Todo.Domain.Common;
using Todo.Domain.Todos;

namespace Todo.Application.Todos.CompleteTodo;

public sealed record CompleteTodoCommand(string OwnerId, Guid Id, int ExpectedVersion);

public sealed class CompleteTodoHandler(ITodoRepository todos, TimeProvider time, ILogger<CompleteTodoHandler> logger)
{
    public async Task<Result<TodoItem>> HandleAsync(CompleteTodoCommand command, CancellationToken cancellationToken)
    {
        ArgumentNullException.ThrowIfNull(command);

        var current = await VersionedWrite.LoadAsync(
            todos, command.OwnerId, command.Id, command.ExpectedVersion, logger, cancellationToken);
        if (!current.IsSuccess)
        {
            return current;
        }

        var next = current.Value.Complete(time.GetUtcNow());
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
