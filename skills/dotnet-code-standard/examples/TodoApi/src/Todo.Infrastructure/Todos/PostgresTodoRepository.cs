using Microsoft.EntityFrameworkCore;
using Todo.Application.Abstractions;
using Todo.Domain.Todos;
using Todo.Infrastructure.Persistence;

namespace Todo.Infrastructure.Todos;

internal sealed class PostgresTodoRepository(TodoDbContext db) : ITodoRepository
{
    public Task<TodoItem?> FindAsync(string ownerId, Guid id, CancellationToken cancellationToken) =>
        db.Todos.AsNoTracking().SingleOrDefaultAsync(todo => todo.Id == id && todo.OwnerId == ownerId, cancellationToken);

    public async Task<Page<TodoItem>> ListAsync(TodoListQuery query, CancellationToken cancellationToken)
    {
        ArgumentNullException.ThrowIfNull(query);

        var filtered = db.Todos.AsNoTracking().Where(todo => todo.OwnerId == query.OwnerId);
        if (query.Status is { } status)
        {
            filtered = filtered.Where(todo => todo.Status == status);
        }

        if (query.Search is { } search)
        {
            var pattern = $"%{EscapeLike(search)}%";
            filtered = filtered.Where(todo => EF.Functions.ILike(todo.Title, pattern, "\\"));
        }

        var total = await filtered.CountAsync(cancellationToken);
        var items = await filtered
            .SortBy(query.Sort)
            .Skip(query.Page.Offset)
            .Take(query.Page.Limit)
            .ToListAsync(cancellationToken);

        return new Page<TodoItem>(items, total, query.Page.Limit, query.Page.Offset);
    }

    public async Task AddAsync(TodoItem todo, CancellationToken cancellationToken)
    {
        db.Todos.Add(todo);
        try
        {
            await db.SaveChangesAsync(cancellationToken);
        }
        finally
        {
            db.Entry(todo).State = EntityState.Detached;
        }
    }

    public async Task<WriteResult> UpdateAsync(TodoItem todo, int expectedVersion, CancellationToken cancellationToken)
    {
        ArgumentNullException.ThrowIfNull(todo);

        var entry = db.Todos.Attach(todo);
        entry.State = EntityState.Modified;
        entry.Property(row => row.OwnerId).IsModified = false;
        entry.Property(row => row.CreatedAt).IsModified = false;
        entry.Property(row => row.Version).OriginalValue = expectedVersion;

        try
        {
            await db.SaveChangesAsync(cancellationToken);
            return WriteResult.Written;
        }
        catch (DbUpdateConcurrencyException)
        {
            return await MissReasonAsync(todo.OwnerId, todo.Id, cancellationToken);
        }
        finally
        {
            entry.State = EntityState.Detached;
        }
    }

    public async Task<WriteResult> DeleteAsync(string ownerId, Guid id, int expectedVersion, CancellationToken cancellationToken)
    {
        var deleted = await db.Todos
            .Where(row => row.Id == id && row.OwnerId == ownerId && row.Version == expectedVersion)
            .ExecuteDeleteAsync(cancellationToken);

        return deleted == 1 ? WriteResult.Written : await MissReasonAsync(ownerId, id, cancellationToken);
    }

    private async Task<WriteResult> MissReasonAsync(string ownerId, Guid id, CancellationToken cancellationToken)
    {
        var current = await db.Todos
            .Where(row => row.Id == id && row.OwnerId == ownerId)
            .Select(row => (int?)row.Version)
            .SingleOrDefaultAsync(cancellationToken);

        return current is { } version ? WriteResult.Mismatch(version) : WriteResult.NotFound;
    }

    private static string EscapeLike(string value) =>
        value.Replace("\\", "\\\\", StringComparison.Ordinal)
            .Replace("%", "\\%", StringComparison.Ordinal)
            .Replace("_", "\\_", StringComparison.Ordinal);
}
