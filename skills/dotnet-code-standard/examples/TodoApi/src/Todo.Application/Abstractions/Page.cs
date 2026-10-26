namespace Todo.Application.Abstractions;

public sealed record PageRequest(int Limit, int Offset)
{
    public const int MaxLimit = 100;
    public const int MaxOffset = 10_000;
}

public sealed record Page<T>(IReadOnlyList<T> Items, int Total, int Limit, int Offset);
