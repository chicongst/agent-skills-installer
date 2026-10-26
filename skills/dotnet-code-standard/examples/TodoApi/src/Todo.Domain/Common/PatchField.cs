namespace Todo.Domain.Common;

public readonly record struct PatchField<T>
{
    private readonly T _value;

    public PatchField(T value)
    {
        _value = value;
        HasValue = true;
    }

    public bool HasValue { get; }

    public T Value => HasValue ? _value : throw new InvalidOperationException("PatchField has no value.");

    public T GetValueOrDefault(T fallback) => HasValue ? _value : fallback;
}
