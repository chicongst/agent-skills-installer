using System.Diagnostics.CodeAnalysis;

namespace Todo.Domain.Common;

public readonly struct Result<T>
{
    private readonly T? _value;

    internal Result(T value)
    {
        _value = value;
        Error = null;
    }

    internal Result(DomainError error)
    {
        _value = default;
        Error = error;
    }

    public DomainError? Error { get; }

    [MemberNotNullWhen(false, nameof(Error))]
    public bool IsSuccess => Error is null;

    public T Value => IsSuccess
        ? _value!
        : throw new InvalidOperationException($"Cannot read the value of a failed result ({Error.Code}).");

    public static implicit operator Result<T>(T value) => new(value);

    public static implicit operator Result<T>(DomainError error) => new(error);
}

public static class Result
{
    public static Result<T> Success<T>(T value) => new(value);

    public static Result<T> Failure<T>(DomainError error) => new(error);
}
