using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Design;

namespace Todo.Infrastructure.Persistence;

internal sealed class DesignTimeTodoDbContextFactory : IDesignTimeDbContextFactory<TodoDbContext>
{
    private const string ConnectionVariable = "TODO_DESIGN_CONNECTION";

    public TodoDbContext CreateDbContext(string[] args)
    {
        var connectionString = Environment.GetEnvironmentVariable(ConnectionVariable)
            ?? throw new InvalidOperationException($"Set {ConnectionVariable} to run EF Core design-time commands.");
        var options = new DbContextOptionsBuilder<TodoDbContext>().UseNpgsql(connectionString).Options;
        return new TodoDbContext(options);
    }
}
