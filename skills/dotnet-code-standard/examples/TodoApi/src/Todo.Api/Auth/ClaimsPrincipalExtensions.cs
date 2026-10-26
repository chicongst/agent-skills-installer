using System.Security.Claims;

namespace Todo.Api.Auth;

internal static class ClaimsPrincipalExtensions
{
    public static string GetOwnerId(this ClaimsPrincipal user) =>
        user.FindFirstValue(ClaimTypes.NameIdentifier)
        ?? throw new InvalidOperationException("The fallback policy guarantees a NameIdentifier claim.");
}
