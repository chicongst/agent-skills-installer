using Microsoft.Extensions.Logging;
using Todo.Application.Abstractions;
using Todo.Domain.Common;
using Todo.Domain.Todos;

namespace Todo.Application.Todos;

internal static class VersionedWrite
{
    public static async Task<Result<TodoItem>> LoadAsync(
        ITodoRepository todos,
        string ownerId,
        Guid id,
        int expectedVersion,
        ILogger logger,
        CancellationToken cancellationToken)
    {
        var todo = await todos.FindAsync(ownerId, id, cancellationToken);
        if (todo is null)
        {
            return TodoErrors.NotFound(id);
        }

        if (todo.Version != expectedVersion)
        {
            TodoLog.VersionConflict(logger, id, expectedVersion, todo.Version);
            return TodoErrors.VersionMismatch(todo.Version);
        }

        return todo;
    }

    public static DomainError? ToError(WriteResult result, Guid id, int expectedVersion, ILogger logger)
    {
        switch (result.Status)
        {
            case WriteStatus.Written:
                return null;
            case WriteStatus.VersionMismatch when result.CurrentVersion is { } current:
                TodoLog.VersionConflict(logger, id, expectedVersion, current);
                return TodoErrors.VersionMismatch(current);
            default:
                return TodoErrors.NotFound(id);
        }
    }
}
