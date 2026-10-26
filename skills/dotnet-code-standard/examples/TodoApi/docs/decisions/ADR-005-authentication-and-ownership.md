# ADR-005: JWT bearer authentication, ownership in the aggregate

Status: accepted

## Context
Without identity any client can read or delete any todo. The long-term plan includes partner and customer access.

## Decision
- `AddAuthentication().AddJwtBearer()` configured from `Authentication:Schemes:Bearer` (Authority, ValidAudiences). A fallback authorization policy requires an authenticated user on every endpoint; only health endpoints opt out with `AllowAnonymous()`.
- `TodoItem.OwnerId` is set from the token subject at creation and never changes. Every repository query filters by owner; another owner's todo is reported as 404, not 403, so ids cannot be probed.
- Writes are rate limited per user (fixed window, 60/min) and return 429 ProblemDetails.
- Local development issues tokens with `dotnet user-jwts create --project src/Todo.Api`; tests replace the scheme with `TestAuthHandler`.

## Consequences
Roles and scopes (staff vs customer vs partner) are added as named policies on endpoint groups when they exist; ownership stays in the domain.

## Notes
- The fallback policy also applies when no route matches, so anonymous callers get 401 for unknown routes and signed-in callers get 404. This hides which routes exist.
- The rate limit is per replica: N replicas allow 60 × N writes per minute per user. Move to a distributed limiter (Redis) or the gateway if that matters.
- `Idempotency-Key` on create is deliberately not implemented: the only client is a first-party UI that does not retry POSTs. Add it (patterns §10) before partner or offline clients call this API.
