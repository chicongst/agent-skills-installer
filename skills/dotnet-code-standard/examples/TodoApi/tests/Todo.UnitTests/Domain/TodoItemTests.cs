using Todo.Domain.Common;
using Todo.Domain.Todos;

namespace Todo.UnitTests.Domain;

public sealed class TodoItemTests
{
    private const string Owner = "user-1";
    private static readonly DateTimeOffset Now = new(2026, 1, 1, 9, 0, 0, TimeSpan.Zero);
    private static readonly DateTimeOffset Later = Now.AddHours(1);

    private static TodoItem NewTodo(TodoPriority? priority = null) =>
        TodoItem.Create(Guid.NewGuid(), Owner, new TodoDraft("Buy milk", null, null, priority), Now).Value;

    [Fact]
    public void Create_TrimsTextAndStartsOpenAtVersionOne()
    {
        var result = TodoItem.Create(Guid.NewGuid(), Owner, new TodoDraft("  Buy milk  ", "   ", null, null), Now);

        Assert.True(result.IsSuccess);
        Assert.Equal("Buy milk", result.Value.Title);
        Assert.Null(result.Value.Description);
        Assert.Equal(TodoStatus.Open, result.Value.Status);
        Assert.Equal(1, result.Value.Version);
        Assert.Equal(Owner, result.Value.OwnerId);
    }

    [Theory]
    [InlineData(null)]
    [InlineData("")]
    [InlineData("   ")]
    public void Create_WithBlankTitle_ReturnsTitleRequired(string? title)
    {
        var result = TodoItem.Create(Guid.NewGuid(), Owner, new TodoDraft(title, null, null, null), Now);

        Assert.Equal(TodoErrors.TitleRequired, result.Error);
    }

    [Fact]
    public void Create_WithTooLongTitle_ReturnsTitleTooLong()
    {
        var draft = new TodoDraft(new string('a', TodoItem.TitleMaxLength + 1), null, null, null);

        var result = TodoItem.Create(Guid.NewGuid(), Owner, draft, Now);

        Assert.Equal(TodoErrors.TitleTooLong, result.Error);
    }

    [Fact]
    public void Create_WithUndefinedPriority_ReturnsPriorityInvalid()
    {
        var result = TodoItem.Create(Guid.NewGuid(), Owner, new TodoDraft("x", null, null, (TodoPriority)3), Now);

        Assert.Equal(TodoErrors.PriorityInvalid, result.Error);
    }

    [Fact]
    public void Create_WithoutOwner_ReturnsOwnerRequired()
    {
        var result = TodoItem.Create(Guid.NewGuid(), " ", new TodoDraft("x", null, null, null), Now);

        Assert.Equal(TodoErrors.OwnerRequired, result.Error);
    }

    [Fact]
    public void Apply_ChangesOnlyProvidedFieldsAndBumpsVersion()
    {
        var todo = NewTodo(TodoPriority.Low);
        var changes = new TodoChanges(
            default,
            default,
            new PatchField<DateOnly?>(new DateOnly(2026, 2, 1)),
            new PatchField<TodoPriority?>(null));

        var changed = todo.Apply(changes, Later).Value;

        Assert.Equal("Buy milk", changed.Title);
        Assert.Null(changed.Priority);
        Assert.Equal(new DateOnly(2026, 2, 1), changed.DueDate);
        Assert.Equal(2, changed.Version);
        Assert.Equal(Later, changed.UpdatedAt);
    }

    [Fact]
    public void Apply_WithNullTitle_ReturnsTitleRequired()
    {
        var result = NewTodo().Apply(new TodoChanges(new PatchField<string?>(null), default, default, default), Later);

        Assert.Equal(TodoErrors.TitleRequired, result.Error);
    }

    [Fact]
    public void Apply_WithNoFields_ReturnsEmptyChanges()
    {
        var result = NewTodo().Apply(new TodoChanges(default, default, default, default), Later);

        Assert.Equal(TodoErrors.EmptyChanges, result.Error);
    }

    [Fact]
    public void Complete_WhenAlreadyDone_KeepsVersion()
    {
        var done = NewTodo().Complete(Later);

        var again = done.Complete(Later.AddMinutes(1));

        Assert.Equal(TodoStatus.Done, again.Status);
        Assert.Equal(done.Version, again.Version);
        Assert.Equal(Later, again.CompletedAt);
    }

    [Fact]
    public void Reopen_ClearsCompletedAtAndBumpsVersion()
    {
        var done = NewTodo().Complete(Now);

        var reopened = done.Reopen(Later);

        Assert.Equal(TodoStatus.Open, reopened.Status);
        Assert.Null(reopened.CompletedAt);
        Assert.Equal(done.Version + 1, reopened.Version);
    }
}
