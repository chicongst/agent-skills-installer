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
