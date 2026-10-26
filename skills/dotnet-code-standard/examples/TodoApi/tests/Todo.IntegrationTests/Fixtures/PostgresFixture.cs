using Microsoft.EntityFrameworkCore;
using Testcontainers.PostgreSql;
using Todo.Infrastructure.Persistence;

[assembly: AssemblyFixture(typeof(Todo.IntegrationTests.Fixtures.PostgresFixture))]

namespace Todo.IntegrationTests.Fixtures;

public sealed class PostgresFixture : IAsyncLifetime
{
    private readonly PostgreSqlContainer _container = new PostgreSqlBuilder("postgres:17-alpine").Build();

    public string ConnectionString => _container.GetConnectionString();

    public TodoDbContext CreateDbContext() =>
        new(new DbContextOptionsBuilder<TodoDbContext>().UseNpgsql(ConnectionString).Options);

    public async ValueTask InitializeAsync()
    {
        await _container.StartAsync();
        await using var db = CreateDbContext();
        await db.Database.MigrateAsync();
    }

    public async ValueTask DisposeAsync() => await _container.DisposeAsync();
}
