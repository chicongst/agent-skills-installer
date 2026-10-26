using System.ComponentModel.DataAnnotations;
using Microsoft.Extensions.Configuration;

namespace Todo.Infrastructure;

public enum StorageDriver
{
    Memory,
    Postgres,
}

public sealed class StorageOptions : IValidatableObject
{
    public const string SectionName = "Storage";

    [Required]
    public StorageDriver? Driver { get; init; }

    public string? ConnectionString { get; init; }

    public IEnumerable<ValidationResult> Validate(ValidationContext validationContext)
    {
        if (Driver == StorageDriver.Postgres && string.IsNullOrWhiteSpace(ConnectionString))
        {
            yield return new ValidationResult(
                $"{SectionName}:{nameof(ConnectionString)} is required when {SectionName}:{nameof(Driver)} is Postgres.",
                [nameof(ConnectionString)]);
        }
    }

    public static StorageOptions Load(IConfiguration configuration)
    {
        var options = configuration.GetSection(SectionName).Get<StorageOptions>()
            ?? throw new InvalidOperationException(
                $"Configuration section '{SectionName}' is missing. Set {SectionName}:{nameof(Driver)} explicitly.");

        Validator.ValidateObject(options, new ValidationContext(options), validateAllProperties: true);
        return options;
    }
}
