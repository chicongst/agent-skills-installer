using Todo.Domain.Todos;

namespace Todo.Application.Abstractions;

public enum WriteStatus
{
    Written,
    NotFound,
    VersionMismatch,
}

public readonly record struct WriteResult(WriteStatus Status, int? CurrentVersion)
{
    public static WriteResult Written => new(WriteStatus.Written, null);

    public static WriteResult NotFound => new(WriteStatus.NotFound, null);

    public static WriteResult Mismatch(int currentVersion) => new(WriteStatus.VersionMismatch, currentVersion);
}

public enum TodoSortField
{
    CreatedAt,
    DueDate,
}

public sealed record TodoSort(TodoSortField Field, bool Descending);

public sealed record TodoListQuery(string OwnerId, TodoStatus? Status, string? Search, TodoSort Sort, PageRequest Page);

public interface ITodoRepository
{
    Task<TodoItem?> FindAsync(string ownerId, Guid id, CancellationToken cancellationToken);

    Task<Page<TodoItem>> ListAsync(TodoListQuery query, CancellationToken cancellationToken);

    Task AddAsync(TodoItem todo, CancellationToken cancellationToken);

    Task<WriteResult> UpdateAsync(TodoItem todo, int expectedVersion, CancellationToken cancellationToken);

    Task<WriteResult> DeleteAsync(string ownerId, Guid id, int expectedVersion, CancellationToken cancellationToken);
}
