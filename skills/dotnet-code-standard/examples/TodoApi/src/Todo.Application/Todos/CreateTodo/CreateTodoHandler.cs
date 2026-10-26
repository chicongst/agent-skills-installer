using Microsoft.Extensions.Logging;
using Todo.Application.Abstractions;
using Todo.Domain.Common;
using Todo.Domain.Todos;

namespace Todo.Application.Todos.CreateTodo;

public sealed record CreateTodoCommand(string OwnerId, TodoDraft Draft);

public sealed class CreateTodoHandler(ITodoRepository todos, TimeProvider time, ILogger<CreateTodoHandler> logger)
{
    public async Task<Result<TodoItem>> HandleAsync(CreateTodoCommand command, CancellationToken cancellationToken)
    {
        ArgumentNullException.ThrowIfNull(command);

        var now = time.GetUtcNow();
        var created = TodoItem.Create(Guid.CreateVersion7(now), command.OwnerId, command.Draft, now);
        if (!created.IsSuccess)
        {
            return created;
        }

        await todos.AddAsync(created.Value, cancellationToken);
        TodoLog.Created(logger, created.Value.Id);
        return created;
    }
}
