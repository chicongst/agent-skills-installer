---
name: api-design
description: Use when designing a new HTTP/REST API or reviewing an API contract (OpenAPI spec, route list, endpoint handlers) — resources and URLs, status codes, error format, pagination, idempotency, concurrency control, auth, rate limiting, versioning and deprecation. Not for overall system or service architecture (use `architect`), database schema and indexes (use `db-design`), writing reference docs for an API that is already designed (use `docs-writer`), or a security audit of the implementation (use `security-review`).
---

# API Design

Design or review an HTTP API contract so that it is predictable for consumers, safe to retry, and safe to evolve. The contract is the deliverable — not the implementation.

## Step 0 — Establish context

Before designing, find or ask for:

- **Mode**: *design* (new API or new endpoints) or *review* (an existing spec, route list, or handlers). In review mode read the actual files; do not review from a description.
- **Consumers**: who calls it (first-party web/mobile, partners, public), and whether they can be forced to upgrade.
- **Existing conventions**: grep the codebase and any existing OpenAPI spec for envelope shape, field casing, ID format, error format, pagination style, auth scheme. **Existing conventions win** over the defaults below; call out a deviation only when it causes a real defect (e.g. two error formats in one API).
- **Constraints**: expected list sizes, write-retry scenarios (mobile networks, payment), multi-tenant data.

If something that changes the contract is unknown (auth model, tenancy, who may delete), ask the user (use AskUserQuestion if available, otherwise ask in plain text). If you proceed anyway, list each assumption under Overview and each unresolved item under Open Questions.

## Defaults (use when the project has no convention)

### Resources and methods
- Plural nouns, lowercase, IDs in the path: `GET /v1/orders/{order_id}`. Actions are methods, not verbs in paths. For a true non-CRUD action, use a sub-resource or an explicit action path (`POST /v1/orders/{id}/cancel`) and say why.
- Nest at most one level, and only for creation/listing under a parent (`POST /projects/{id}/tasks`); give the child a top-level path for reads if clients need to address it directly.
- Method semantics (RFC 9110 §9): GET/HEAD safe; GET, PUT, DELETE idempotent; POST not idempotent. PATCH (RFC 5789) is not guaranteed idempotent — specify the patch format: JSON Merge Patch (RFC 7396, `application/merge-patch+json`) for simple partial updates.
- Success codes: `200` with body, `201 Created` + `Location` header for creates, `202 Accepted` + status resource for async work, `204 No Content` for deletes with no body.

### Representations
- Pick one field casing (snake_case or camelCase) and one timestamp format (RFC 3339 UTC, e.g. `2026-09-20T08:00:00Z`) for the whole API.
- Opaque string IDs; never expose sequential DB IDs to untrusted clients if enumeration matters.
- Single resources are returned as the object itself; lists as `{ "data": [...], "next_cursor": ... }`. Clients must ignore unknown fields — state that in the contract so adding fields stays non-breaking.
- Enums: list every value. Money: integer minor units plus currency code, never floats.

### Errors — RFC 9457 Problem Details
Use `Content-Type: application/problem+json` (RFC 9457, which obsoletes RFC 7807). Standard members: `type` (URI identifying the problem type; defaults to `about:blank`), `title`, `status`, `detail`, `instance`. Add extension members for machine use, e.g. `errors` (per-field) and `request_id`. One error format for every endpoint, including 404s from the router and 500s from middleware.

Status code rules:

| Status | Use for |
|---|---|
| 400 | Malformed syntax: unparseable JSON, wrong JSON type, bad query-param format, missing required `Idempotency-Key` |
| 401 | Missing/invalid credentials. MUST include `WWW-Authenticate` (RFC 9110 §15.5.2) |
| 403 | Authenticated but not allowed. Return 404 instead when revealing existence is itself a leak |
| 404 | Resource does not exist (or is hidden from this caller) |
| 409 | Conflict with current state (duplicate unique value, invalid state transition, same idempotency key still in flight) |
| 412 | `If-Match` precondition failed (stale ETag) |
| 415 | Unsupported `Content-Type` |
| 422 | Well-formed but semantically invalid: value out of range, unknown enum value, date in the past, referenced entity not usable, idempotency key reused with a different payload |
| 428 | Precondition required: `If-Match` missing on an endpoint that requires it (RFC 6585) |
| 429 | Rate limited; send `Retry-After` |
| 500 | Server bug; never leak stack traces or SQL |
| 503 | Temporary unavailability; send `Retry-After` |

### Pagination and filtering
- **Pick one style for the whole API.** Default: cursor pagination — `?limit=` (with a documented default and max) and `?cursor=`; response `next_cursor` is `null` on the last page. The cursor is opaque to clients and encodes the last row's sort key plus a unique tiebreaker (e.g. `created_at, id`), so inserts don't shift pages.
- Offset/page pagination is acceptable only for small, rarely-changing lists where "jump to page N" is a real requirement; if chosen, it is used everywhere.
- Don't return `total` by default (a `COUNT` over a large filtered set is expensive); offer it only if a real UI needs it.
- Filters are query params named after fields (`?status=done&assignee_id=...`); sorting via `?sort=created_at` / `?sort=-created_at` from a documented allow-list. No list endpoint is unbounded.

### Idempotency (retry safety)
- Accept an `Idempotency-Key` request header on POST (and on PATCH if clients retry it). The header is an IETF httpapi draft (draft-ietf-httpapi-idempotency-key-header), not yet an RFC; its recommended behaviour is:
  - same key + same payload → replay the stored original response;
  - same key + different payload → `422`;
  - original request still processing → `409`;
  - key missing where the endpoint requires one → `400`.
- Store key + request fingerprint + response, scoped per caller, with a documented expiry (e.g. 24 h — state it as a choice, not a standard).

### Concurrency (lost updates)
- Return an `ETag` on every response that carries the resource representation (GET, POST create, PUT, PATCH). PUT/PATCH on resources several clients edit take `If-Match: <etag>`; stale → `412`; missing when required → `428`. Add it to DELETE too when deleting a just-changed resource would lose someone's work.
- Don't use `If-Unmodified-Since` as the only guard — one-second resolution loses same-second writes.

### Auth
- Default: OAuth 2.0 bearer tokens (RFC 6750) in the `Authorization` header, never in the query string. Server-to-server may use API keys, still in a header.
- Every endpoint lists its required scope/role in the Resources table; anything public is marked explicitly. Fail closed.
- Enforce object-level authorization on every ID in the path or body (OWASP API1:2023 Broken Object Level Authorization) — e.g. the caller must be a member of the project that owns the task.

### Rate limiting
- Over the limit → `429 Too Many Requests` (RFC 6585 §4) with `Retry-After` (RFC 9110 §10.2.3; seconds or HTTP-date) and a problem+json body.
- Advertise quota with the `RateLimit` / `RateLimit-Policy` fields from the IETF httpapi ratelimit-headers draft (not yet an RFC), or follow the project's existing `X-RateLimit-*` headers. Label the header set as a choice.
- Limits are numbers the user must supply; if none are given, mark them as assumptions.

### Versioning and deprecation
- Major version in the URL (`/v1`) or a header — pick one. Bump the major version only for breaking changes.
- **Breaking**: removing/renaming a field or endpoint, changing a type or meaning, adding a required request field, adding an enum value clients must handle, tightening validation, changing status codes or error `type`s. **Non-breaking**: new endpoints, new optional request fields, new response fields.
- To retire something: send `Deprecation: @<unix-seconds>` (RFC 9745, a structured-field Date) plus `Link: <doc-url>; rel="deprecation"`, and `Sunset: <HTTP-date>` (RFC 8594) no earlier than the deprecation date. Publish a migration guide before the Deprecation date.

## Review mode

Check the contract against every Defaults section above (as adapted to the project's conventions) and against itself. Tag each finding with the shared severity scale:

- **🔴 BLOCKER** — broken contract or security hole: missing object-level authz, unbounded list, non-retry-safe payment/create endpoint, breaking change without a version bump.
- **🟠 MAJOR** — inconsistency or gap that will bite soon: two pagination styles, two error formats, wrong status codes, no concurrency control on shared writes.
- **🟡 MINOR** — naming/casing drift, missing `Location`, undocumented limits.
- **💭 NIT** — taste; mention briefly.

Each finding cites the location (`file:line`, or `METHOD /path` in a spec) and gives the concrete fix (the corrected route, status code, header or body).

## Output format

Omit **Findings** in design mode. In review mode, fill the other sections with the contract as it should be after fixes. A worked example is in `examples/example.txt` (if installed). `template.md` mirrors this format.

```markdown
# API Design: [Service/Feature Name]

## Overview
- **Purpose**: [what the API enables]
- **Consumers**: [who calls it]
- **Assumptions**: [each assumption made in Step 0, or "none"]

## Conventions
- **Base URL & versioning**: [e.g. https://api.example.com/v1 — URL major version]
- **Auth**: [scheme, where the credential goes, scope model]
- **Format**: [media types, field casing, ID format, timestamp format]

## Resources
### [Resource Name]
| Method | Path | Description | Auth (scope) | Idempotent | Success |
|--------|------|-------------|--------------|------------|---------|

**Fields**: [field — type — constraints; enum values listed in full]

## Request/Response Examples
[Raw HTTP request and response (status line, key headers, body) for: a create, a list, a conditional update, and an error]

## Errors
[Problem Details format with one example body]
| Status | type | When |
|--------|------|------|

## Pagination & Filtering
[Style, parameters, default/max limit, sort key + tiebreaker, filters, sort options]

## Idempotency & Concurrency
[Which endpoints take Idempotency-Key and If-Match, key scope/expiry, resulting status codes]

## Rate Limiting
[Limits (or marked assumptions), 429 behaviour, headers]

## Versioning & Deprecation
[What counts as breaking, deprecation/sunset process and headers, migration guide location]

## Design Decisions
**[Decision]** — [why, and the alternative rejected]

## Open Questions
- [Question the user must answer before this ships]

## Findings (review mode only)
### 🔴 BLOCKER / 🟠 MAJOR / 🟡 MINOR / 💭 NIT — [title]
**Location**: [file:line or METHOD /path]
**Problem**: [what is wrong and the consumer impact]
**Fix**: [concrete corrected contract]
```

## Rules
1. Examples use only facts from the user's input; invented numbers (limits, expiries, windows) are labelled as assumptions.
2. Cite RFCs only for what they actually define; label IETF drafts as drafts.
