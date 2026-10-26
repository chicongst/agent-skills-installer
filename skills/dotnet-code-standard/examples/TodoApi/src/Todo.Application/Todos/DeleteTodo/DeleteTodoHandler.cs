using Microsoft.Extensions.Logging;
using Todo.Application.Abstractions;
using Todo.Domain.Common;

namespace Todo.Application.Todos.DeleteTodo;

public sealed record DeleteTodoCommand(string OwnerId, Guid Id, int ExpectedVersion);

public sealed class DeleteTodoHandler(ITodoRepository todos, ILogger<DeleteTodoHandler> logger)
{
    public async Task<DomainError?> HandleAsync(DeleteTodoCommand command, CancellationToken cancellationToken)
    {
        ArgumentNullException.ThrowIfNull(command);

        var written = await todos.DeleteAsync(command.OwnerId, command.Id, command.ExpectedVersion, cancellationToken);
        var error = VersionedWrite.ToError(written, command.Id, command.ExpectedVersion, logger);
        if (error is null)
        {
            TodoLog.Deleted(logger, command.Id);
        }

        return error;
    }
}
