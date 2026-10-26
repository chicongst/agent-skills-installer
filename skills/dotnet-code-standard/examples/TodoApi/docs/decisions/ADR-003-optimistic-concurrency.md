# ADR-003: Optimistic concurrency with Version + ETag + If-Match

Status: accepted

## Context
Two users can edit the same todo. Last-write-wins silently loses data.

## Decision
Every todo has an integer `Version`. Reads return `ETag: "<version>"`. PATCH, complete, reopen and DELETE require `If-Match`: missing or `*` → 428, weak (`W/"3"`) → 412 (weak tags never match under RFC 9110 strong comparison), malformed → 400, stale → 412 with `currentVersion`. The EF repository attaches the new state with `Version` as concurrency token and the expected value as original value, so `SaveChangesAsync` issues one `UPDATE … WHERE id = @id AND version = @expected` covering every mapped column; deletes use `ExecuteDeleteAsync` with the same predicate. On a miss the repository returns the current version in the same call, so the handler never re-reads.

## Consequences
Clients must keep the ETag from their last read. Completing an already completed todo is a no-op that returns 200 and the unchanged ETag.
