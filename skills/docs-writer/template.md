<!-- Use the skeleton for your doc type, then append Writer's notes (not part of the published doc). Mirrors SKILL.md "Output Format". -->

<!-- README / setup guide -->
# [Project name]
[One line: what it does and who it is for]
**Last verified**: [commit or version — YYYY-MM-DD]

## Prerequisites
| Tool | Version | Check with |
|---|---|---|

## Setup
### 1. [Install / Configure / Run]
[command block + expected result]

## Verify it works
[command + expected output]

## Troubleshooting
**`[exact error text]`** — [cause]. [Fix command or action]

## Related
- [link]

<!-- How-to guide -->
# How to [goal]
[One line: when you need this]

## Prerequisites
- [tool / access / permission]

## Steps
### 1. [Action]
[why, only if non-obvious] + [command block] + [expected result]

## Verify it worked
[check]

## Undo
[how to reverse the steps]

## Troubleshooting
**`[exact error text]`** — [cause]. [Fix]

<!-- API reference (repeat Endpoint per endpoint) -->
# [API name]
[One line: what it does and who calls it]
**Last verified**: [commit or version — YYYY-MM-DD]

## Authentication
[scheme, header, how to obtain credentials]

## [METHOD] [path]
[One line: what it does]

### Parameters
| Name | In | Type | Required | Constraints |
|---|---|---|---|---|

### Request example
[runnable command]

### Response — [status]
[example body + field table if non-obvious]

### Errors
| Status | Code | Cause | Fix |
|---|---|---|---|

## Troubleshooting
**[symptom]** — [cause]. [Fix]

<!-- ADR -->
# ADR-[N]: [Decision title]
**Status**: [Proposed / Accepted / Deprecated / Superseded by ADR-N]
**Date**: [YYYY-MM-DD]
**Deciders**: [names or team]

## Context
[forces, constraints, facts]

## Decision
We will [decision].

## Alternatives considered
- **[Option]** — rejected because [concrete reason]

## Consequences
- Positive: [...]
- Negative: [...]
- Follow-up: [...]

<!-- Writer's notes -->
## Writer's notes
**Doc type / audience**: [type] / [audience, or "assumed: …"]
**Sources**: [files, specs, or input sections each fact came from]
**Verified**: [command → observed result], or "none — [reason]"
**Not run**: [commands left unverified and why]
**Open questions**: [each `[TODO: confirm …]` in the doc, plus code/input discrepancies found]
