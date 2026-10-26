using Todo.Application.Abstractions;
using Todo.Domain.Todos;

namespace Todo.UnitTests.Fakes;

internal sealed class FakeTodoRepository : ITodoRepository
{
    private readonly Dictionary<Guid, TodoItem> _rows = [];
    private readonly Lock _gate = new();

    public Task<TodoItem?> FindAsync(string ownerId, Guid id, CancellationToken cancellationToken)
    {
        lock (_gate)
        {
            return Task.FromResult(_rows.GetValueOrDefault(id) is { } todo && todo.OwnerId == ownerId ? todo : null);
        }
    }

    public Task<Page<TodoItem>> ListAsync(TodoListQuery query, CancellationToken cancellationToken)
    {
        lock (_gate)
        {
            var owned = _rows.Values.Where(todo => todo.OwnerId == query.OwnerId).OrderBy(todo => todo.Id).ToList();
            var items = owned.Skip(query.Page.Offset).Take(query.Page.Limit).ToList();
            return Task.FromResult(new Page<TodoItem>(items, owned.Count, query.Page.Limit, query.Page.Offset));
        }
    }

    public Task AddAsync(TodoItem todo, CancellationToken cancellationToken)
    {
        lock (_gate)
        {
            _rows.Add(todo.Id, todo);
        }

        return Task.CompletedTask;
    }

    public Task<WriteResult> UpdateAsync(TodoItem todo, int expectedVersion, CancellationToken cancellationToken)
    {
        lock (_gate)
        {
            if (!_rows.TryGetValue(todo.Id, out var current) || current.OwnerId != todo.OwnerId)
            {
                return Task.FromResult(WriteResult.NotFound);
            }

            if (current.Version != expectedVersion)
            {
                return Task.FromResult(WriteResult.Mismatch(current.Version));
            }

            _rows[todo.Id] = todo;
            return Task.FromResult(WriteResult.Written);
        }
    }

    public Task<WriteResult> DeleteAsync(string ownerId, Guid id, int expectedVersion, CancellationToken cancellationToken)
    {
        lock (_gate)
        {
            if (!_rows.TryGetValue(id, out var current) || current.OwnerId != ownerId)
            {
                return Task.FromResult(WriteResult.NotFound);
            }

            if (current.Version != expectedVersion)
            {
                return Task.FromResult(WriteResult.Mismatch(current.Version));
            }

            _rows.Remove(id);
            return Task.FromResult(WriteResult.Written);
        }
    }
}
