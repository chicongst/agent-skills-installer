---
name: mastery
description: "Use when writing or modifying code in any language — a silent baseline of senior engineering defaults (errors, bounded queries, idempotency, concurrency, security, testability). When a task-specific skill applies it leads and this only fills gaps: refactor/dotnet-code-refactor, fix-bug/debug, test-writer, ui-design, db-design, api-design. Never overrides the project's conventions or CLAUDE.md. Not for reviewing or auditing code — use code-review, pr-review, code-audit, or dotnet-code-review."
---

# Senior Engineering Defaults

Apply these silently while writing code. Do not announce them, emit a checklist, or add a report — the code is the output. Skip any rule that does not fit the language or context.

## Precedence

1. **The project wins.** CLAUDE.md, lint/format config, and patterns already in the codebase override everything below. Read neighboring code before writing: match its error style, logger, naming, test framework, and folder layout.
2. **A task-specific skill wins next** — `refactor`/`dotnet-code-refactor`, `fix-bug`/`debug`, `test-writer`, `ui-design`, `db-design`, `api-design`. Use this skill only for what that skill does not cover.
3. **These defaults** apply to whatever is left.

If a rule here conflicts with the project, follow the project. If following the project would introduce a real defect (SQL injection, lost data), say so in one line instead of silently deviating.

## Scope discipline

- Change only what the task needs. No drive-by renames, reformatting, or "while I'm here" refactors in the same change.
- Keep behavior changes separate from restructuring. If a fix requires a behavior change the user did not ask for (new pagination, different error message, time zone handling), state it explicitly.
- Match rigor to context: a throwaway script skips defensive layers; money, auth, quotas, and data writes never do. When unsure, treat business logic as production.
- State non-obvious assumptions in one or two lines after the code (e.g., "assumes `last_login` is `timestamptz`"). If the answer would change the design, ask first — use AskUserQuestion if available, otherwise ask in plain text.

## Simplicity

- Write the plain function first. Add an interface, strategy, or factory only when a second real implementation exists now.
- Duplicate until the third occurrence with the same contract, then extract.
- No unused parameters, constants, imports, or config knobs. Every name you add must be read somewhere.
- Wrap a third-party dependency only at a boundary where the wrapper adds value: a narrower interface, error translation, a test seam, or a swap that is actually needed. A pass-through proxy is an anti-pattern.
- Before writing a helper, search the codebase for an existing one.

## Errors

- Validate at trust boundaries (request input, files, env, third-party responses) and fail fast with a message naming the field and the problem.
- Catch the specific errors you can handle. A catch-all is acceptable only at a top-level boundary (request handler, job runner, main loop) that logs and converts to a response or exit code.
- Never swallow: log with context, re-raise, or return an explicit error value — whichever the codebase already uses.
- Retry only transient failures, only on idempotent operations, with capped exponential backoff plus jitter and an overall deadline.

## Data access

- Parameterize every query; never build SQL, shell commands, or paths by string concatenation of input.
- Select explicit columns; avoid `SELECT *` in production queries.
- Every list query is bounded. For large or mutable sets use keyset pagination (`WHERE id > :last_id ORDER BY id LIMIT :n`); offset only for small, stable sets.
- No N+1: join, batch-load, or use the ORM's eager loading.
- Process large datasets in bounded chunks with a resumable cursor; batch small writes instead of one round-trip per row.
- Multi-statement writes that must succeed together go in one transaction.
- For index and schema decisions, use `db-design`.

## Concurrency and idempotency

- Never read-then-write shared state without protection. Prefer an atomic statement (`UPDATE stock SET qty = qty - 1 WHERE id = :id AND qty > 0`, then check affected rows); otherwise a row lock or an optimistic version check.
- Operations that can be retried or re-run (jobs, webhooks, message handlers, payment calls) must be idempotent: a processed marker, a unique constraint, or an idempotency key.
- Run independent I/O concurrently; sequential awaits on unrelated calls add latency for nothing.
- Every network call and every async task has a timeout or cancellation path.

## Security

- No secrets in code, logs, or error messages. Read them from the environment or a secret manager.
- Never log tokens, passwords, or PII; log stable IDs instead.
- Passwords: argon2id or bcrypt through a maintained library. Never a fast hash, never hand-rolled crypto.
- Check authorization on every access to a resource, not just authentication at the edge.

## Time, config, observability

- Store and compare time in UTC with timezone-aware types (Python: `datetime.now(timezone.utc)`, not the deprecated `datetime.utcnow()`). Convert to local time only for display.
- Inject the clock or pass "now" as a parameter when logic depends on time.
- Config comes from the environment or config files, validated at startup; missing required values fail fast. Local named constants are fine for values that never vary by environment.
- Use the project's logger. Log one line per business event with stable IDs and outcome; errors carry enough context to reproduce.

## Testability

- Pass dependencies (DB connection, HTTP client, clock, email service) in instead of constructing them inside business logic.
- Keep I/O at the edges and decisions in pure functions.
- No module-level mutable state.

## Structure

- Follow the project's existing folder layout. If none exists, group by feature or domain rather than by technical layer.
- One unit, one reason to change; if you cannot name it precisely, it does too much.
- Prefer guard clauses to nesting deeper than three levels.
- Adding a dependency needs a reason the standard library or existing dependencies cannot cover; update the lockfile with it.

A worked example is in `examples/example.txt` (if installed).
