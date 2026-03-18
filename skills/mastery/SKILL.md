---
name: mastery
description: Use when writing, modifying, or generating any code — automatically applies senior-level engineering principles regardless of programming language.
---

# Senior Engineering Principles

You internalize these principles and apply them silently when writing code. Do not announce or checklist — just write better code. Skip any principle that does not exist or is irrelevant in the current language or context.

## Context Awareness

Assess before writing:

- **Prototype / script / PoC** — keep it simple, skip defensive layers, optimize for speed
- **Production / shared codebase** — apply full rigor: error handling, edge cases, validation, logging
- **Unclear** — default to production-level for business logic, prototype-level for exploratory code

Let context drive complexity. Never over-engineer a throwaway script. Never under-engineer a payment flow.

## Concurrency & Async

- Prefer async/await (or language equivalent) over raw callbacks or manual thread management
- Identify shared mutable state and protect it — mutex, lock, atomic, channel, or immutable design
- Avoid race conditions: never assume ordering without explicit synchronization
- Use structured concurrency where available (task groups, coroutine scope, context cancellation)
- Handle cancellation and timeout explicitly — never let async work run unbounded
- Prefer message passing over shared memory when crossing boundaries

## Error Handling

- Fail fast at system boundaries — validate input early, reject invalid state immediately
- Use the language's idiomatic error mechanism (exceptions, Result/Either, error return, Option)
- Never swallow errors silently — log, propagate, or handle with explicit intent
- Distinguish recoverable vs fatal errors — retry transient failures, crash on corruption
- Include context in errors — what failed, with what input, why it matters
- Avoid catch-all handlers in business logic — catch specific errors, let unexpected ones bubble

## Retry & Resilience

- Use exponential backoff with jitter for transient failures (network, rate limit, lock contention)
- Set max retry count and total timeout — never retry forever
- Apply circuit breaker pattern for external dependencies — fail fast when downstream is unhealthy
- Make operations idempotent before adding retry — retry without idempotency causes duplication
- Log each retry attempt with context for observability

## Caching

- Cache at the right layer — in-memory for hot path, distributed (Redis, Memcached) for shared state
- Every cache entry needs an invalidation strategy — TTL, event-driven, or write-through
- Guard against cache stampede — use locking, request coalescing, or stale-while-revalidate
- Never cache sensitive data without encryption and access control
- Consider cache warming for cold start scenarios

## Batch Processing & Chunking

- Process large datasets in chunks — never load unbounded data into memory
- Choose chunk size based on memory constraints and downstream throughput
- Use streaming/cursor-based iteration over full collection loading when possible
- Handle partial failures within batches — track progress, support resume from last checkpoint
- Apply backpressure — slow down producers when consumers can't keep up

## Smart Batching

- Aggregate many small operations into a single larger operation to reduce per-operation overhead
- Apply to: DB bulk insert/update instead of per-row writes, API calls consolidated into batch endpoints, message queue flush instead of per-message send, DataLoader pattern for N+1 resolution
- Collect items over a short time window (or until a size threshold) then flush as one batch — not one-by-one
- Always handle partial batch failures — know which items succeeded and which failed, don't retry the whole batch blindly
- Tune batch size and flush interval together — too small loses efficiency, too large increases latency and memory pressure
- Distinguish from Chunking: Chunking splits large data down for safe processing; Smart Batching groups small operations up for efficient execution

## Pagination

- Use cursor-based pagination for large or real-time datasets — offset-based breaks with mutations
- Always set a maximum page size — never let clients request unbounded results
- Return pagination metadata (next cursor, has_more) in response
- For offset pagination, be aware of performance degradation at high offsets

## Query & Data Access

- Prevent N+1 queries — use eager loading, batch loading (DataLoader pattern), or joins
- Select only needed columns — avoid `SELECT *` in production code
- Index columns used in WHERE, JOIN, ORDER BY — but don't over-index (write penalty)
- Use query parameterization — never concatenate user input into queries
- Set query timeouts — a missing WHERE clause shouldn't take down the database
- Profile queries in development — slow queries are bugs

## Performance

- Measure before optimizing — use profilers, flame graphs, benchmarks, not intuition
- Optimize the hot path — 80/20 rule, focus on what runs most frequently
- Watch for hidden allocations — string concatenation in loops, unnecessary object creation
- Use appropriate data structures — hash maps for lookup, sorted structures for range queries
- Prefer lazy evaluation / streaming for large data — don't materialize what you don't need
- Set and monitor memory budgets for long-running processes — prevent silent memory leaks

## Security Fundamentals

- Validate and sanitize all external input — user input, API payloads, file uploads, URL parameters
- Use parameterized queries — never build SQL/NoSQL queries from string concatenation
- Apply principle of least privilege — services, DB users, API keys get minimum required permissions
- Never hardcode secrets — use environment variables, secret managers, or vault
- Hash passwords with modern algorithms (bcrypt, argon2) — never MD5/SHA for passwords
- Set security headers, CORS policies, and rate limits at API boundaries
- Audit authentication and authorization separately — authn confirms identity, authz confirms permission

## Logging & Observability

- Use structured logging (JSON) with consistent fields: timestamp, level, correlation/trace ID, context
- Log at appropriate levels — ERROR for failures needing action, WARN for degraded state, INFO for business events, DEBUG for development
- Never log sensitive data — passwords, tokens, PII, credit card numbers
- Include request context — who, what, when, duration, outcome
- Add metrics for business-critical operations — not just system health
- Ensure logs are grep-friendly — searchable by trace ID across services

## Configuration Management

- Externalize all configuration — no magic numbers, no hardcoded URLs, no embedded credentials
- Validate configuration at startup — fail fast with clear error if required config is missing
- Use typed/schema-validated config (zod, pydantic, viper) — not raw string parsing
- Support environment-specific overrides without code changes
- Document every config option — what it does, valid values, default

## Code Organization

- One module/class = one responsibility — if you can't name it clearly, it does too much
- Keep functions short and focused — a function that needs a comment block to explain flow is too long
- Minimize public API surface — expose only what consumers need, hide implementation details
- Group by feature/domain, not by technical layer — `user/` over `controllers/`, `services/`, `models/`
- Avoid deep nesting — early return, guard clauses, extract helper functions

## SOLID Principles

- **Single Responsibility** — a class/module changes for one reason only
- **Open/Closed** — extend behavior through composition or polymorphism, not modifying existing code
- **Liskov Substitution** — subtypes must be drop-in replacements without breaking callers
- **Interface Segregation** — many small interfaces over one large one; clients shouldn't depend on methods they don't use
- **Dependency Inversion** — depend on abstractions, not concretions; inject dependencies, don't instantiate them

In languages without classes/interfaces (C, shell, some scripting languages), apply the underlying ideas: separation of concerns, modularity, clear contracts between components.

## Design Patterns

Apply when they simplify — never force a pattern where a simple function would do:

- **Singleton** — one instance globally (DB pool, config, logger). Prefer DI over global access
- **Factory** — centralize object creation when the exact type depends on runtime input
- **Builder** — construct complex objects step-by-step when constructors have too many parameters
- **Adapter** — wrap third-party APIs behind your own interface for testability and swap-ability
- **Decorator / Middleware** — layer behavior (logging, auth, caching) without modifying core logic
- **Facade** — simplified interface to a complex subsystem (payment gateway, email service)
- **Strategy** — swap algorithms at runtime without modifying consumers (parsers, validators, payment processors)
- **Observer / Event Emitter** — decouple producers from consumers for event-driven flows
- **Repository** — abstract data access behind a clean interface; swap storage without changing business logic
- **DTO** — decouple internal models from external API contracts. Never expose database entities directly

In languages without classes, use closures, higher-order functions, or module patterns to achieve the same decoupling.

## DRY, KISS, YAGNI

- **DRY** — extract when duplication exceeds 3 occurrences AND the abstraction is stable. Premature DRY is worse than duplication.
- **KISS** — choose the simplest solution that works. Complexity is a cost, not a feature.
- **YAGNI** — don't build for hypothetical future requirements. Add extension points only when the second use case arrives.

Three similar lines of code is better than a premature abstraction.

## Dependency Management

- Pin dependency versions in production — `1.2.3` not `^1.2.3`
- Review changelogs before upgrading — especially major versions
- Minimize dependency count — every dependency is a supply chain risk
- Wrap third-party libraries behind your own interface — isolate blast radius of breaking changes
- Audit dependencies for known vulnerabilities regularly

## Testing Awareness

When writing code, make it testable by default:

- Inject dependencies — don't hardcode database connections, API clients, or file paths
- Keep side effects at the edges — pure business logic in the core, I/O at the boundaries
- Return values instead of mutating state — easier to assert, easier to reason about
- Write small functions with clear inputs and outputs — each function is a testable unit
- Avoid global/static mutable state — it makes tests order-dependent and flaky
