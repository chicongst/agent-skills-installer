using Todo.Application.Abstractions;
using Todo.Domain.Common;
using Todo.Domain.Todos;
using Todo.Infrastructure.Todos;
using Todo.IntegrationTests.Fixtures;

namespace Todo.IntegrationTests.Persistence;

public sealed class PostgresTodoRepositoryTests(PostgresFixture postgres)
{
    private static readonly DateTimeOffset Now = new(2026, 1, 1, 9, 0, 0, TimeSpan.Zero);
    private readonly string _owner = $"user-{Guid.NewGuid():N}";

    private static CancellationToken Ct => TestContext.Current.CancellationToken;

    private TodoItem NewTodo(string title) =>
        TodoItem.Create(Guid.CreateVersion7(), _owner, new TodoDraft(title, null, null, null), Now).Value;

    private static TodoItem Renamed(TodoItem todo, string title) =>
        todo.Apply(new TodoChanges(new PatchField<string?>(title), default, default, default), Now.AddMinutes(1)).Value;

    [Fact]
    public async Task UpdateAsync_WritesEveryChangedColumn()
    {
        var todo = NewTodo("Buy milk");
        await using (var db = postgres.CreateDbContext())
        {
            await new PostgresTodoRepository(db).AddAsync(todo, Ct);
        }

        var next = todo.Apply(
            new TodoChanges(
                new PatchField<string?>("Buy oat milk"),
                new PatchField<string?>("2 litres"),
                new PatchField<DateOnly?>(new DateOnly(2026, 2, 1)),
                new PatchField<TodoPriority?>(TodoPriority.High)),
            Now.AddMinutes(1)).Value.Complete(Now.AddMinutes(2));

        await using (var db = postgres.CreateDbContext())
        {
            Assert.Equal(WriteStatus.Written, (await new PostgresTodoRepository(db).UpdateAsync(next, 1, Ct)).Status);
        }

        await using var read = postgres.CreateDbContext();
        Assert.Equal(next, await new PostgresTodoRepository(read).FindAsync(_owner, todo.Id, Ct));
    }

    [Fact]
    public async Task UpdateAsync_TwoContextsRacingOnSameVersion_ExactlyOneWins()
    {
        var todo = NewTodo("Buy milk");
        await using (var db = postgres.CreateDbContext())
        {
            await new PostgresTodoRepository(db).AddAsync(todo, Ct);
        }

        await using var first = postgres.CreateDbContext();
        await using var second = postgres.CreateDbContext();
        var results = await Task.WhenAll(
            new PostgresTodoRepository(first).UpdateAsync(Renamed(todo, "A"), 1, Ct),
            new PostgresTodoRepository(second).UpdateAsync(Renamed(todo, "B"), 1, Ct));

        Assert.Single(results, result => result.Status == WriteStatus.Written);
        Assert.Single(results, result => result is { Status: WriteStatus.VersionMismatch, CurrentVersion: 2 });
    }

    [Fact]
    public async Task DeleteAsync_ForAnotherOwner_ReturnsNotFoundAndKeepsRow()
    {
        var todo = NewTodo("Buy milk");
        await using var db = postgres.CreateDbContext();
        var repository = new PostgresTodoRepository(db);
        await repository.AddAsync(todo, Ct);

        var result = await repository.DeleteAsync("someone-else", todo.Id, 1, Ct);

        Assert.Equal(WriteStatus.NotFound, result.Status);
        Assert.NotNull(await repository.FindAsync(_owner, todo.Id, Ct));
    }
}
