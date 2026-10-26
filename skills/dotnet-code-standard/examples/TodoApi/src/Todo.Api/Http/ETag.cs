using System.Globalization;
using System.Text.RegularExpressions;

namespace Todo.Api.Http;

internal static partial class ETag
{
    public static string From(int version) => $"\"{version.ToString(CultureInfo.InvariantCulture)}\"";

    public static IfMatch Parse(string? header)
    {
        var value = header?.Trim();
        if (string.IsNullOrEmpty(value))
        {
            return IfMatch.Of(IfMatchState.Missing);
        }

        if (value == "*")
        {
            return IfMatch.Of(IfMatchState.Wildcard);
        }

        if (value.StartsWith("W/", StringComparison.Ordinal))
        {
            return IfMatch.Of(IfMatchState.Weak);
        }

        var match = StrongETag().Match(value);
        return match.Success && int.TryParse(match.Groups[1].Value, CultureInfo.InvariantCulture, out var version)
            ? new IfMatch(IfMatchState.Valid, version)
            : IfMatch.Of(IfMatchState.Malformed);
    }

    [GeneratedRegex("^\"(\\d{1,9})\"$")]
    private static partial Regex StrongETag();
}

internal readonly record struct IfMatch(IfMatchState State, int Version)
{
    public static IfMatch Of(IfMatchState state) => new(state, 0);
}

internal enum IfMatchState
{
    Missing,
    Wildcard,
    Weak,
    Malformed,
    Valid,
}
