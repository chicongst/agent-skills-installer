using Todo.Application.Abstractions;
using Todo.Domain.Todos;

namespace Todo.Infrastructure.Todos;

internal sealed class InMemoryTodoRepository : ITodoRepository
{
    private readonly Dictionary<Guid, TodoItem> _rows = [];
    private readonly Lock _gate = new();

    public Task<TodoItem?> FindAsync(string ownerId, Guid id, CancellationToken cancellationToken)
    {
        lock (_gate)
        {
            return Task.FromResult(FindOwned(ownerId, id));
        }
    }

    public Task<Page<TodoItem>> ListAsync(TodoListQuery query, CancellationToken cancellationToken)
    {
        ArgumentNullException.ThrowIfNull(query);

        lock (_gate)
        {
            var matches = _rows.Values
                .Where(todo => todo.OwnerId == query.OwnerId)
                .Where(todo => query.Status is null || todo.Status == query.Status)
                .Where(todo => query.Search is null || todo.Title.Contains(query.Search, StringComparison.OrdinalIgnoreCase))
                .AsQueryable()
                .SortBy(query.Sort)
                .ToList();

            var items = matches.Skip(query.Page.Offset).Take(query.Page.Limit).ToList();
            return Task.FromResult(new Page<TodoItem>(items, matches.Count, query.Page.Limit, query.Page.Offset));
        }
    }

    public Task AddAsync(TodoItem todo, CancellationToken cancellationToken)
    {
        ArgumentNullException.ThrowIfNull(todo);

        lock (_gate)
        {
            if (!_rows.TryAdd(todo.Id, todo))
            {
                throw new InvalidOperationException($"Todo {todo.Id} already exists.");
            }
        }

        return Task.CompletedTask;
    }

    public Task<WriteResult> UpdateAsync(TodoItem todo, int expectedVersion, CancellationToken cancellationToken)
    {
        ArgumentNullException.ThrowIfNull(todo);

        lock (_gate)
        {
            var result = Check(todo.OwnerId, todo.Id, expectedVersion);
            if (result.Status == WriteStatus.Written)
            {
                _rows[todo.Id] = todo;
            }

            return Task.FromResult(result);
        }
    }

    public Task<WriteResult> DeleteAsync(string ownerId, Guid id, int expectedVersion, CancellationToken cancellationToken)
    {
        lock (_gate)
        {
            var result = Check(ownerId, id, expectedVersion);
            if (result.Status == WriteStatus.Written)
            {
                _rows.Remove(id);
            }

            return Task.FromResult(result);
        }
    }

    private TodoItem? FindOwned(string ownerId, Guid id) =>
        _rows.TryGetValue(id, out var todo) && todo.OwnerId == ownerId ? todo : null;

    private WriteResult Check(string ownerId, Guid id, int expectedVersion)
    {
        var current = FindOwned(ownerId, id);
        if (current is null)
        {
            return WriteResult.NotFound;
        }

        return current.Version == expectedVersion ? WriteResult.Written : WriteResult.Mismatch(current.Version);
    }
}
