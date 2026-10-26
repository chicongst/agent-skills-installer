# ADR-002: Optimistic concurrency with version, ETag and If-Match

**Status:** accepted

## Context
Two users editing the same todo at the same time must not silently overwrite each other.

## Decision
- Every todo carries `version` (1 on create, +1 on each real change); responses send `ETag: "<version>"`.
- PATCH, complete, reopen and DELETE require `If-Match` with exactly one strong ETag: missing or `*` → 428, weak → 412, malformed or a list → 400, stale → 412 with `currentVersion`.
- The service checks the version after loading, then the repository writes only if the stored version still equals the expected one (under an `asyncio.Lock` in memory; `UPDATE … WHERE version = :expected` in SQL). A writer that slips in between load and write therefore still gets 412.
- A no-op change returns the current state without writing or bumping the version, so other clients' ETags stay valid.

## Consequences
Clients must send the ETag they last read and reload on 412. Proven by `test_patch_ten_concurrent_writers_with_same_etag_exactly_one_wins` and the lost-race unit test.
