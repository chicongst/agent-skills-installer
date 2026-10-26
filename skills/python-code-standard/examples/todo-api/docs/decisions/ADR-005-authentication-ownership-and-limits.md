# ADR-005: Authentication, ownership and write limits

**Status:** accepted

## Decision
- Bearer JWT verified with PyJWT: explicit algorithm list, typed so settings accept only asymmetric algorithms (`RS256`, `PS256`, `ES256`, `EdDSA`), required `exp`, `iss`, `aud`, 30 s leeway. Keys from `TODO_AUTH__JWKS_URL` (cached `PyJWKClient`, fetched off the event loop) or `TODO_AUTH__PUBLIC_KEY_FILE` for local development (`scripts/dev_token.py`). No HS256 shared secret, no default issuer.
- `CurrentOwner` (`web/auth.py`) returns the token `sub`. No/invalid token → 401 with `WWW-Authenticate: Bearer`; valid token whose `sub` is missing, blank, padded with whitespace, longer than the owner column (128) or contains NUL → 403, so one person can never map to two owners and the database never sees an id it cannot store.
- Every route in the todos router depends on it; a unit test fails if one does not.
- Ownership lives in the aggregate (`owner_id`) and in every repository query. Another owner's todo is 404, never 403, so ids do not leak.
- Writes are limited per user (`limits` moving window, default `60/minute`) → 429 with `Retry-After`. Storage is in memory, so the limit is **per replica**; switch `MemoryStorage` for Redis when running more than one.
- Unknown routes return 404 for everyone (FastAPI routes before auth); acceptable because no resource is revealed.
- `Idempotency-Key` on create is **not** implemented: the only client is a first-party UI that refreshes after a failed create. Add it before partner integrations, queue consumers or offline-sync clients call `POST /v1/todos`.
