# ADR-004: Authentication, ownership and write limits

**Status:** accepted

## Decision
- Bearer JWT verified with PyJWT: asymmetric algorithms only, required `exp`/`iss`/`aud`, keys from JWKS (fetched off the event loop) or a public-key file in development. No token or invalid token → 401; a valid token without a usable `sub` → 403.
- Every todo route depends on `CurrentOwner`; a unit test walks the router's dependants to prove it. Every repository call is scoped to the owner; another owner's todo is 404.
- Writes are limited per user with a `limits` moving window held in memory, so the limit is **per replica**. Use a shared storage (Redis) before running several replicas.
- `Idempotency-Key` on create is **not** implemented: the intended client is a first-party UI that refreshes the list after a failed create. Add it before partners, queue consumers or offline-sync clients call `POST /v1/todos`.
- Not versioned for partners yet beyond the `/v1` prefix.
