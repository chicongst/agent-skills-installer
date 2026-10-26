using System.Text.Json;
using System.Text.Json.Serialization;
using Todo.Domain.Common;

namespace Todo.Api.Http;

internal sealed class PatchFieldJsonConverterFactory : JsonConverterFactory
{
    public override bool CanConvert(Type typeToConvert) =>
        typeToConvert.IsGenericType && typeToConvert.GetGenericTypeDefinition() == typeof(PatchField<>);

    public override JsonConverter CreateConverter(Type typeToConvert, JsonSerializerOptions options)
    {
        var valueType = typeToConvert.GetGenericArguments()[0];
        return (JsonConverter)Activator.CreateInstance(typeof(PatchFieldJsonConverter<>).MakeGenericType(valueType))!;
    }

    private sealed class PatchFieldJsonConverter<T> : JsonConverter<PatchField<T>>
    {
        public override bool HandleNull => true;

        public override PatchField<T> Read(ref Utf8JsonReader reader, Type typeToConvert, JsonSerializerOptions options)
        {
            try
            {
                return new(JsonSerializer.Deserialize<T>(ref reader, options)!);
            }
            catch (JsonException ex)
            {
                throw new JsonException(ex.Message, ex);
            }
        }

        public override void Write(Utf8JsonWriter writer, PatchField<T> value, JsonSerializerOptions options) =>
            JsonSerializer.Serialize(writer, value.GetValueOrDefault(default!), options);
    }
}
