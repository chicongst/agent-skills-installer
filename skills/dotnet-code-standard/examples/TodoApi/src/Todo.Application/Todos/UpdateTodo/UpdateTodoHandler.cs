using Microsoft.Extensions.Logging;
using Todo.Application.Abstractions;
using Todo.Domain.Common;
using Todo.Domain.Todos;

namespace Todo.Application.Todos.UpdateTodo;

public sealed record UpdateTodoCommand(string OwnerId, Guid Id, int ExpectedVersion, TodoChanges Changes);

public sealed class UpdateTodoHandler(ITodoRepository todos, TimeProvider time, ILogger<UpdateTodoHandler> logger)
{
    public async Task<Result<TodoItem>> HandleAsync(UpdateTodoCommand command, CancellationToken cancellationToken)
    {
        ArgumentNullException.ThrowIfNull(command);

        var current = await VersionedWrite.LoadAsync(
            todos, command.OwnerId, command.Id, command.ExpectedVersion, logger, cancellationToken);
        if (!current.IsSuccess)
        {
            return current;
        }

        var next = current.Value.Apply(command.Changes, time.GetUtcNow());
        if (!next.IsSuccess)
        {
            return next;
        }

        var written = await todos.UpdateAsync(next.Value, command.ExpectedVersion, cancellationToken);
        return VersionedWrite.ToError(written, command.Id, command.ExpectedVersion, logger) is { } error ? error : next;
    }
}
