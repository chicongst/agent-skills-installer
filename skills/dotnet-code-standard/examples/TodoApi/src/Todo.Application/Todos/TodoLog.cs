using Microsoft.Extensions.Logging;

namespace Todo.Application.Todos;

internal static partial class TodoLog
{
    [LoggerMessage(Level = LogLevel.Information, Message = "Todo {TodoId} created")]
    public static partial void Created(ILogger logger, Guid todoId);

    [LoggerMessage(Level = LogLevel.Information, Message = "Todo {TodoId} deleted")]
    public static partial void Deleted(ILogger logger, Guid todoId);

    [LoggerMessage(
        Level = LogLevel.Warning,
        Message = "Version conflict on todo {TodoId}: expected {ExpectedVersion}, current {CurrentVersion}")]
    public static partial void VersionConflict(ILogger logger, Guid todoId, int expectedVersion, int? currentVersion);
}
