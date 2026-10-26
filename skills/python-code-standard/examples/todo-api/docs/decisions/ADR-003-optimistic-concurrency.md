# ADR-003: Optimistic concurrency with version, ETag and If-Match

**Status:** accepted

## Context
Two clients editing the same todo must not silently overwrite each other. Polar uses pessimistic `SELECT … FOR UPDATE`, which holds locks across the request and does not help a client that read the row minutes ago.

## Decision
- Every todo has `version` (starts at 1, +1 on each real change). Responses carry `ETag: "<version>"`.
- Writes require `If-Match`: missing or `*` → 428, weak → 412, malformed → 400, stale → 412 with `currentVersion`.
- The SQL repository writes with `UPDATE … WHERE id = :id AND owner_id = :owner AND version = :expected RETURNING version`; no row → one follow-up `SELECT version` in the same transaction distinguishes 404 from 412. The values come from `tables.to_values(todo)`, which reads every mapped column from the aggregate, so a new column cannot be left out of an update.
- The in-memory repository does the same check under an `asyncio.Lock`.
- A no-op — completing a done todo, or a PATCH whose values equal the current ones — returns the current state without writing or bumping the version, so other clients' ETags stay valid.
- `If-Match` takes exactly one strong ETag; a list is 400 `INVALID_IF_MATCH`.

## Consequences
Clients must send the ETag they read. Proven by `test_patch_ten_concurrent_writers_with_same_etag_exactly_one_wins` on both backends and a two-session race in `test_sql_repository.py`.
