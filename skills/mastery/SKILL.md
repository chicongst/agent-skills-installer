---
name: mastery
description: Use when writing, modifying, or generating any code — automatically applies senior-level engineering principles regardless of programming language.
---

# Senior Engineering Principles

You internalize these principles and apply them silently while writing code. Do not announce them, do not emit a checklist, do not produce a report — just write better code. Skip any principle that does not exist or is irrelevant in the current language or context.

This skill covers what you decide *while typing*. For deep dives, defer to the dedicated skill instead of duplicating its judgment here:

| Topic | Skill |
|-------|-------|
| Schema, index design, query plans | `db-design` |
| Profiling, benchmarking, optimization tradeoffs | `performance-review` |
| Threat modeling, vulnerability review | `security-review` |
| Service boundaries, messaging topology, failure design | `architect` |
| Endpoint contracts, versioning, pagination shape | `api-design` |
| Test strategy and coverage design | `test-writer` |

## Context Awareness

Assess before writing:

- **Prototype / script / PoC** — keep it simple, skip defensive layers, optimize for speed
- **Production / shared codebase** — apply full rigor: error handling, edge cases, validation, logging
- **Unclear** — default to production-level for business logic, prototype-level for exploratory code

Let context drive complexity. Never over-engineer a throwaway script. Never under-engineer a payment flow.

## KISS, YAGNI, DRY

- **KISS** — choose the simplest solution that works. Complexity is a cost, not a feature.
- **YAGNI** — don't build for hypothetical future requirements. Add extension points only when the second use case arrives.
- **DRY** — extract when duplication exceeds 3 occurrences AND the abstraction is stable. Premature DRY is worse than duplication.

Three similar lines of code beat a premature abstraction. Reach for a design pattern only when a plain function has already failed — a pattern applied to one variant is over-engineering, not craft.

## Error Handling

- Fail fast at system boundaries — validate input early, reject invalid state immediately
- Use the language's idiomatic error mechanism (exceptions, Result/Either, error return, Option)
- Never swallow errors silently — log, propagate, or handle with explicit intent
- Distinguish recoverable vs fatal errors — retry transient failures, crash on corruption
- Include context in errors — what failed, with what input, why it matters
- Avoid catch-all handlers in business logic — catch specific errors, let unexpected ones bubble

## Concurrency & Async

- Prefer async/await (or language equivalent) over raw callbacks or manual thread management
- Identify shared mutable state and protect it — mutex, lock, atomic, channel, or immutable design
- Never assume ordering without explicit synchronization
- Use structured concurrency where available (task groups, coroutine scope, context cancellation)
- Handle cancellation and timeout explicitly — never let async work run unbounded
- Run independent async work concurrently; sequential `await` on unrelated calls is a latency bug
- **Never read-then-write without holding a lock.** Between the read and the write, another transaction can mutate the same row — this is how oversell and lost updates happen. Use an atomic operation (`UPDATE stock SET qty = qty - 1 WHERE qty > 0`), a pessimistic lock when contention is high, or an optimistic version check when conflicts are rare.

## Retry & Resilience

- Make an operation idempotent *before* adding retry — retry without idempotency causes duplication
- Exponential backoff with jitter for transient failures; always set a max attempt count and total timeout
- Circuit-break external dependencies — fail fast when downstream is unhealthy
- Log each retry attempt with context

## Caching

- Cache at the right layer — in-memory for hot path, distributed for shared state
- Every cache entry needs an invalidation strategy — TTL, event-driven, or write-through
- Guard against stampede — locking, request coalescing, or stale-while-revalidate
- Never cache sensitive data without encryption and access control

## Bounded Data Movement

Two opposite problems, both solved by never moving data one row at a time:

- **Chunk large data down** — process big datasets in bounded chunks, stream or paginate with a cursor, never load unbounded results into memory. Handle partial failure: track progress, support resume from the last checkpoint.
- **Batch small operations up** — bulk insert instead of per-row writes, batch endpoints instead of per-item calls, DataLoader instead of N+1. Flush on a size threshold or a short time window.
- Apply backpressure — slow producers when consumers cannot keep up
- Tune size and interval together — too small loses efficiency, too large adds latency and memory pressure
- Know which item in a batch failed; never blindly retry the whole batch

## Query & Data Access

- Prevent N+1 — eager load, batch load, or join
- Select only the columns you need; never `SELECT *` in production code
- Always parameterize — never concatenate user input into a query
- Set query timeouts — a missing WHERE clause should not take down the database
- Every list query needs a limit. Cursor pagination (`WHERE id > last_seen`) for large sets; offset only for small ones
- Run EXPLAIN on any non-trivial query before shipping it. For index design and query-plan analysis, use `db-design`.

## Security Fundamentals

- Validate and sanitize all external input — request bodies, headers, uploads, URL parameters
- Parameterized queries only
- Least privilege for services, DB users, and API keys
- Never hardcode secrets — environment variables, secret manager, or vault
- Hash passwords with bcrypt or argon2 — never MD5/SHA
- Security headers, CORS policy, and rate limits at API boundaries
- Authentication and authorization are separate checks — confirm identity, then confirm permission

## Logging & Observability

- Structured logging (JSON) with consistent fields: timestamp, level, correlation/trace ID, context
- Log levels mean something: ERROR needs action, WARN is degraded state, INFO is a business event, DEBUG is for development
- Never log secrets, tokens, or PII
- Include request context — who, what, when, duration, outcome
- Add metrics for business-critical operations, not just system health

## Configuration Management

- Externalize all configuration — no magic numbers, no hardcoded URLs, no embedded credentials
- Validate configuration at startup — fail fast with a clear error if required config is missing
- Use typed/schema-validated config, not raw string parsing
- Document every option — what it does, valid values, default

## Code Organization

- One module/class = one responsibility — if you cannot name it clearly, it does too much
- Keep functions short and focused — a function needing a comment block to explain its flow is too long
- Minimize public API surface — expose only what consumers need
- Group by feature/domain, not by technical layer — `user/` over `controllers/`, `services/`, `models/`
- Avoid deep nesting — early return, guard clauses, extract helpers

### SOLID
- **Single Responsibility** — a module changes for one reason only
- **Open/Closed** — extend through composition or polymorphism, not by editing existing code
- **Liskov Substitution** — subtypes are drop-in replacements
- **Interface Segregation** — many small interfaces over one large one
- **Dependency Inversion** — depend on abstractions; inject dependencies, don't instantiate them

In languages without classes or interfaces, apply the underlying ideas: separation of concerns, modularity, clear contracts. Use closures, higher-order functions, or module patterns for the same decoupling.

## Dependency Management

- Pin versions in production — `1.2.3`, not `^1.2.3`
- Review changelogs before upgrading, especially major versions
- Minimize dependency count — every dependency is a supply chain risk
- Wrap third-party libraries behind your own interface to isolate the blast radius of breaking changes

## Testing Awareness

Make code testable by default:

- Inject dependencies — no hardcoded connections, clients, clocks, or file paths
- Keep side effects at the edges — pure business logic in the core, I/O at the boundaries
- Return values instead of mutating state
- Write small functions with clear inputs and outputs
- Avoid global/static mutable state — it makes tests order-dependent and flaky
