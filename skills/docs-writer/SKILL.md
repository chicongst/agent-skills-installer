---
name: docs-writer
description: Use when writing or updating technical documentation from code, specs, or notes — README/setup guides, how-to guides, API references, ADRs, usage instructions — or when syncing existing docs after a code change. Triggers include "write docs", "document this API", "write a README", "write an ADR", "viết tài liệu", "viết README". Not for critiquing an existing document (use `document-review`), release notes or changelog entries (use `changelog`), or designing/reviewing an API contract (use `api-design` — this skill documents behavior that already exists).
---

# Docs Writer

Write documentation a reader can act on, where every fact traces back to the code or the input and every command has been run or is labeled as not run.

A worked example is in `examples/example.txt` (if installed). `template.md` mirrors the output format below.

## Step 0 — Pin down scope before writing

1. **Doc type** — pick exactly one: README/setup guide, how-to, API reference, ADR. One doc answers one question; if the request mixes "how to deploy" with "why we chose X", write two docs (how-to + ADR) or ask which one.
2. **Audience** — who acts on it and what they already know (frontend engineer calling the API, new backend hire, on-call operator, future maintainer). This decides what you explain and what you skip. If not stated, assume a competent engineer new to this project and say so in Writer's notes.
3. **Source of truth** — the code paths, config, spec, or user notes you will derive facts from. If the user gave only a one-line description and no code, ask for the code or spec (use AskUserQuestion if available, otherwise ask in plain text). If they want a draft anyway, write it with every unsourced fact marked `[TODO: confirm …]`.
4. **Existing docs** — search for docs that already cover the topic (README, `docs/`, wiki links in the repo). Update the existing doc instead of creating a competing one.

## Fact rules (non-negotiable)

1. **Derive every fact from the code or the input.** Versions, limits, ports, env var names, flags, endpoints, status codes, error codes, field names, defaults — each one must be traceable. Do not fill gaps with typical values ("usually port 8080", "tokens expire in 1 hour").
2. **Mark unknowns, never invent.** Write `[TODO: confirm <what> — <why unknown>]` inline and list it under Open questions. A visible gap is fixable; a plausible invention is a bug the reader ships.
3. **Run the commands you document** when it is safe: local, read-only or disposable-state, no production credentials, no cost. Record each command and its observed result in Writer's notes. Never run deploys, migrations against shared databases, destructive commands, or anything touching production — list those as "not run".
4. **Document actual behavior, not intended behavior.** If the code contradicts the input ("max 10 MB" but the limit constant is 5 MB) or looks wrong (errors returned with 200), document what the code does and flag the discrepancy to the user. Do not silently "fix" it in prose.
5. **One status per error, one name per concept.** Each error code maps to exactly one HTTP status; each concept keeps one term throughout (don't alternate "token" / "API key" / "credential").

## Where facts live in a codebase

Follow the project's existing layout; these are common places, not guarantees.

| Fact | Look in |
|---|---|
| Runtime / tool versions | `engines` in `package.json`, `.nvmrc`, `.tool-versions`, `go.mod`, `pyproject.toml`, `Dockerfile` `FROM` |
| Install / build / test / run commands | `package.json` scripts, `Makefile`, `justfile`, CI workflow files (CI is the most reliable record of the real setup order) |
| Env vars and defaults | `.env.example`, config loader (grep `process.env`, `os.getenv`, `os.Getenv`, `Environment.GetEnvironmentVariable`) |
| Ports, base URLs | server bootstrap, config files, `docker-compose.yml` |
| Endpoints, params, validation | route definitions, request schemas/validators, OpenAPI spec |
| Status codes and error codes | handlers, error middleware, exception mappers, and the tests that assert them |
| Error messages for troubleshooting | the literal strings the code throws or logs — quote them so readers can search |

## Writing commands readers can paste

- One command per line, no leading `$` prompt, language-tagged code block (`bash`, `json`, …).
- Placeholders are `<UPPER_SNAKE>` or env vars, and each is explained where first used ("`<TOKEN>` — your API token, see Prerequisites"). Never ship a real-looking secret.
- Show the expected output (or the key line of it) after commands whose success is not obvious.
- State the working directory and OS when it matters; note shell-specific syntax (e.g. `export` vs `set` on Windows `cmd`).
- Commands that change state get a way to undo or check them (how to stop the server, drop the local DB, delete the uploaded object).

## Per-type rules

**README / setup guide** — First line: what it is and who it's for. Prerequisites list exact versions from the repo plus the command to check each (`node --version`). Steps: install → configure → run → verify, each with the command and what success looks like. Troubleshooting comes from failures you actually hit while verifying, plus the error strings the config loader produces for missing env vars. Link out to how-tos rather than growing the README.

**How-to guide** — One goal in the title ("How to rotate the signing key"). Prerequisites include access/permissions, not just tools. Each numbered step is one action + command + expected result. End with "Verify it worked" and, if steps change state, "Undo". Explain *why* only where a reader would otherwise skip or reorder a step.

**API reference** — Per endpoint: method + path, auth, parameters table (name, location, type, required, constraints), a runnable request example, success response per status, errors table (status, code, cause, how to fix). Response and error examples must match the shapes the code builds — no fields the code doesn't return. Order of validation matters when a request can fail several ways; state it if the code makes it deterministic. Prefer linking to a generated spec (OpenAPI) when one exists and keeping prose to what the spec can't say.

**ADR** — Records one decision; immutable once Accepted. Status is `Proposed`, `Accepted`, `Deprecated`, or `Superseded by ADR-<N>`; to change a decision, write a new ADR and update only the old one's status. Context states the forces and constraints as facts (with numbers only if the input has them). Decision is one active sentence ("We will …"). Alternatives list each option with the concrete reason it lost. Consequences include the negative ones and the follow-up work. If the user didn't give the rationale, ask — an ADR with invented reasons is worse than none.

## Keeping docs in sync with code

- When a change renames or removes an env var, flag, endpoint, field, command, or version, grep every doc (and code comments, examples, CI) for the old name and update them in the same change.
- Put each value in one place; elsewhere, link to it. A port repeated in five docs will be wrong in four.
- Add a "Last verified" line (commit or version + date) to setup guides and API references so readers can judge staleness.
- If a section cannot be kept accurate, replace it with a link to the source of truth rather than leaving it to rot.

## Style

Lead with the answer. Second person, imperative, active voice ("Run `make test`", not "The tests should be run"). Tables for anything with more than two attributes per item. Cut sentences that don't change what the reader does. Keep the doc as long as the task requires and no longer.

## Output Format

Deliver the document using the skeleton for its type, then Writer's notes (for the requester — not part of the published doc). Omit a skeleton section only when it truly does not apply (e.g. no Undo for a read-only how-to) and say so in Writer's notes.

````markdown
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
````

```markdown
## Writer's notes
**Doc type / audience**: [type] / [audience, or "assumed: …"]
**Sources**: [files, specs, or input sections each fact came from]
**Verified**: [command → observed result], or "none — [reason]"
**Not run**: [commands left unverified and why]
**Open questions**: [each `[TODO: confirm …]` in the doc, plus code/input discrepancies found]
```
