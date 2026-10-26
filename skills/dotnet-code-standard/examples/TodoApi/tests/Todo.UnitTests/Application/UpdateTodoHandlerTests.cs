using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.Extensions.Time.Testing;
using Todo.Application.Todos.CreateTodo;
using Todo.Application.Todos.UpdateTodo;
using Todo.Domain.Common;
using Todo.Domain.Todos;
using Todo.UnitTests.Fakes;

namespace Todo.UnitTests.Application;

public sealed class UpdateTodoHandlerTests
{
    private const string Owner = "user-1";
    private readonly FakeTodoRepository _todos = new();
    private readonly FakeTimeProvider _time = new(new DateTimeOffset(2026, 1, 1, 9, 0, 0, TimeSpan.Zero));
    private readonly UpdateTodoHandler _handler;

    public UpdateTodoHandlerTests()
    {
        _handler = new UpdateTodoHandler(_todos, _time, NullLogger<UpdateTodoHandler>.Instance);
    }

    private static CancellationToken Ct => TestContext.Current.CancellationToken;

    private async Task<TodoItem> CreateAsync()
    {
        var create = new CreateTodoHandler(_todos, _time, NullLogger<CreateTodoHandler>.Instance);
        var draft = new TodoDraft("Buy milk", null, null, null);
        return (await create.HandleAsync(new CreateTodoCommand(Owner, draft), Ct)).Value;
    }

    private static UpdateTodoCommand Rename(Guid id, int expectedVersion, string title, string owner = Owner) =>
        new(owner, id, expectedVersion, new TodoChanges(new PatchField<string?>(title), default, default, default));

    [Fact]
    public async Task HandleAsync_WithCurrentVersion_PersistsNextVersion()
    {
        var todo = await CreateAsync();
        _time.Advance(TimeSpan.FromMinutes(5));

        var result = await _handler.HandleAsync(Rename(todo.Id, 1, "Buy oat milk"), Ct);

        Assert.Equal(2, result.Value.Version);
        Assert.Equal(_time.GetUtcNow(), result.Value.UpdatedAt);
        Assert.Equal("Buy oat milk", (await _todos.FindAsync(Owner, todo.Id, Ct))?.Title);
    }

    [Fact]
    public async Task HandleAsync_WithStaleVersion_ReturnsVersionMismatchWithCurrentVersion()
    {
        var todo = await CreateAsync();
        await _handler.HandleAsync(Rename(todo.Id, 1, "First"), Ct);

        var result = await _handler.HandleAsync(Rename(todo.Id, 1, "Second"), Ct);

        Assert.Equal(ErrorKind.VersionMismatch, result.Error?.Kind);
        Assert.Equal(2, result.Error?.Details?["currentVersion"]);
    }

    [Fact]
    public async Task HandleAsync_ForAnotherOwner_ReturnsNotFound()
    {
        var todo = await CreateAsync();

        var result = await _handler.HandleAsync(Rename(todo.Id, 1, "Hijack", owner: "user-2"), Ct);

        Assert.Equal(ErrorKind.NotFound, result.Error?.Kind);
    }

    [Fact]
    public async Task HandleAsync_TwoConcurrentWritersWithSameVersion_ExactlyOneWins()
    {
        var todo = await CreateAsync();

        var results = await Task.WhenAll(
            Task.Run(() => _handler.HandleAsync(Rename(todo.Id, 1, "User A"), Ct), Ct),
            Task.Run(() => _handler.HandleAsync(Rename(todo.Id, 1, "User B"), Ct), Ct));

        Assert.Single(results, result => result.IsSuccess);
    }
}
