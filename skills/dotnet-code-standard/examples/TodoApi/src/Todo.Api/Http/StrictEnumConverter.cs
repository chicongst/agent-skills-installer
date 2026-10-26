using System.Text.Json;
using System.Text.Json.Serialization;

namespace Todo.Api.Http;

internal sealed class StrictEnumConverterFactory : JsonConverterFactory
{
    public override bool CanConvert(Type typeToConvert) => typeToConvert.IsEnum;

    public override JsonConverter CreateConverter(Type typeToConvert, JsonSerializerOptions options) =>
        (JsonConverter)Activator.CreateInstance(typeof(StrictEnumConverter<>).MakeGenericType(typeToConvert))!;

    private sealed class StrictEnumConverter<TEnum> : JsonConverter<TEnum>
        where TEnum : struct, Enum
    {
        private static readonly Dictionary<string, TEnum> ByName = Enum.GetValues<TEnum>()
            .ToDictionary(value => JsonNamingPolicy.CamelCase.ConvertName(value.ToString()), StringComparer.Ordinal);

        private static readonly Dictionary<TEnum, string> ByValue = ByName.ToDictionary(pair => pair.Value, pair => pair.Key);

        public override TEnum Read(ref Utf8JsonReader reader, Type typeToConvert, JsonSerializerOptions options)
        {
            if (reader.TokenType == JsonTokenType.String && ByName.TryGetValue(reader.GetString()!, out var value))
            {
                return value;
            }

            throw new JsonException($"Expected one of: {string.Join(", ", ByName.Keys)}.");
        }

        public override void Write(Utf8JsonWriter writer, TEnum value, JsonSerializerOptions options) =>
            writer.WriteStringValue(ByValue[value]);
    }
}
