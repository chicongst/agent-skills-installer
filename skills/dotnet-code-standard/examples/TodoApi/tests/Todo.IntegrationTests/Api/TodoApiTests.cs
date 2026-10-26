using Todo.IntegrationTests.Fixtures;

namespace Todo.IntegrationTests.Api;

public sealed class InMemoryTodoApiTests : TodoApiContract
{
    private protected override TodoApiFactory CreateFactory() => TodoApiFactory.InMemory();
}

public sealed class PostgresTodoApiTests(PostgresFixture postgres) : TodoApiContract
{
    private protected override TodoApiFactory CreateFactory() => TodoApiFactory.Postgres(postgres.ConnectionString);
}
