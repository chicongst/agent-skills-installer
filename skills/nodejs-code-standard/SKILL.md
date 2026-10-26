---
name: nodejs-code-standard
description: Use when writing, scaffolding, or modifying Node.js or TypeScript backend code — HTTP APIs, services, workers, CLIs, package.json/tsconfig/eslint setup — or when the user asks for production-grade, "chuẩn", large-project-quality Node.js code. Not for browser/React UI code (use `ui-design`), reviewing existing code only (use `code-review`), or other languages.
---

# Node.js Code Standard

Write Node.js the way the most-starred Node projects do: small layered modules, validated boundaries, typed errors, structured logs, graceful shutdown, and a test + lint + typecheck gate. **"It works" is not done. Done = `npm run check` passes.**

Project conventions and CLAUDE.md win over this skill. Read 2–3 neighbouring files before adding code to an existing repo.

## Sources (stars checked 2026-10-26)

| Repo | ★ | What we take from it |
|---|---|---|
| nodejs/node | 123k | `node:` imports, `error.code`, `node:test`, `AbortSignal`, no sync I/O on hot paths |
| goldbergyoni/nodebestpractices | 106k | Component folders, app/server split, operational vs programmer errors, fail-fast config |
| nestjs/nest | 77k | Feature modules, constructor DI, `<name>.<role>.ts` file naming |
| expressjs/express | 70k | Central error middleware, thin handlers |
| prisma/orm | 48k | Strict TS, repository-style data access |
| colinhacks/zod | 44k | Validate untrusted input at the boundary, infer types from schemas |
| fastify/fastify | 37k | Plugin encapsulation, JSON-schema validation + response serialization, `inject()` tests |
| pinojs/pino | 18k | JSON logs, child loggers, redaction |

## Rules (non-negotiable)

**Structure** — full tree and dependency table: `examples/todo-api/README.md`
1. Entry files: `main.ts` (config → container → app → listen → signals), `app.ts` (builds the framework instance, no `listen`; tests use it), `container.ts` (composition root — the only place that `new`s infrastructure).
2. One folder per business module under `src/modules/<name>/`, split into layers:
   - `domain/` — entity types and pure rule functions (`createTodo`, `markDone`). No I/O, no async, no framework imports.
   - `application/ports/` — interfaces the use cases need (`TodoRepository`).
   - `application/use-cases/` — one class per action, one file each (`update-todo.ts` → `UpdateTodo.execute()`).
   - `infrastructure/` — port implementations (`postgres-todo.repository.ts`, `in-memory-todo.repository.ts`).
   - `http/` — routes + schemas only; parse, call one use case, shape the reply.
   - `<name>.module.ts` — builds the module's use cases from injected deps.
3. Dependencies point inward: `http → application → domain`; `infrastructure` implements `application/ports`. Enforce with ESLint `no-restricted-imports` per layer (see the example's `eslint.config.js`).
4. `src/shared/` holds cross-module pieces with no business meaning (errors, http helpers, clock, ids, pagination, db pool, lifecycle). If it knows what a "todo" is, it belongs in the module.
5. Instances are created once per container and passed through constructors. No module-level mutable singletons, no `import`ing a concrete repository into a use case. Clock and id generator are injected so tests are deterministic. Each test builds a fresh container.
6. Domain errors carry a `kind` (`not_found`, `version_mismatch`, …), never an HTTP status; the HTTP error handler maps kind → status.
7. Scale to the task: a port/interface exists only when there are two real implementations (here: memory + Postgres). A one-off script or tiny service keeps the module folder but may merge layers — say so in one line.

**Config**
8. Read `process.env` in exactly one file (`config/env.ts`). Parse, validate, `Object.freeze`, fail fast at startup with a clear message. `Number(x) || 3000` is forbidden — it silently accepts garbage.
9. Secrets never get defaults and never get logged. Commit `.env.example`, ignore `.env`.

**Errors**
10. Throw only `Error` subclasses with a stable machine `code` (Node core style: `err.code === 'ERR_...'`). Wrap with `{ cause }`, never lose the original.
11. Operational errors (not found, conflict, timeout) → typed `AppError` → 4xx. Programmer errors → 500 with a generic message, full detail only in logs.
12. One central error handler produces one error shape: `{ error: { code, message, details?, requestId } }` — including framework errors (malformed JSON, 413) and unknown routes (`setNotFoundHandler`).
13. `unhandledRejection`/`uncaughtException` → log fatal and exit. Never keep running in an unknown state.

**Async**
14. `async/await` only. No floating promises (`no-floating-promises` enforces it); mark fire-and-forget with `void` and attach handling.
15. Run independent awaits with `Promise.all`. Every outbound call (fetch/undici/DB) has a timeout: `AbortSignal.timeout(ms)`.
16. No `*Sync` fs/crypto/zlib, no huge `JSON.parse`, no unbounded loops in request paths — the event loop is shared by every request.

**Input/output**
17. Validate every request body, params and query with a schema (`additionalProperties: false`, length limits, `format: 'date'|'date-time'|'email'|'uuid'`). Bodies are validated strictly: no type coercion, unknown fields rejected with 400 (Fastify's defaults coerce and silently strip — override them, see `src/shared/http/validator-compiler.ts`). Nullable fields use `type: ['string', 'null']`. Declare response schemas so internal fields cannot leak.
18. Set a body size limit. Never build SQL/shell/paths by string concatenation with user input.

**Logging**
19. Structured JSON logger (pino; Fastify ships it). No `console.log` in `src/` (lint rule `no-console`). Log with context objects: `log.info({ customerId }, 'customer created')`. Redact `authorization`, `cookie`, passwords, tokens.

**Lifecycle**
20. On `SIGTERM`/`SIGINT`: stop accepting, `await app.close()`, close DB pools, exit 0; force-exit after a timeout (`timer.unref()`).

**Tooling**
21. `"type": "module"`, `node:` prefix for built-ins, `engines.node` + `.nvmrc`, lockfile committed, `npm ci` in CI. Scripts run `.ts` with `node --experimental-strip-types --disable-warning=ExperimentalWarning` (works on Node ≥ 22.6; the flag is a no-op once type stripping is on by default).
22. TypeScript `strict` + `noUncheckedIndexedAccess`; erasable syntax only (no `enum`, `namespace`, parameter properties) so Node runs `.ts` directly. ESLint flat config with `typescript-eslint` `strictTypeChecked`.
23. Scripts: `dev`, `start`, `test`, `typecheck`, `lint`, `check` (all three). Run `check` before saying you are done.

**Testing**
24. `node:test` + `node:assert/strict` (or the repo's runner). Test through the HTTP layer with `app.inject()` — no real port. Fresh app per test, no shared state. Cover happy path, validation failure, not found, conflict, and each business rule.

**Naming**
25. Files `kebab-case` with role suffix (`todo.routes.ts`, `postgres-todo.repository.ts`; use cases are verbs: `update-todo.ts`); classes `PascalCase`; functions/vars `camelCase`; constants `UPPER_SNAKE_CASE`; booleans `is/has/should`. Units in names: `timeoutMs`, `sizeBytes`.

**Data integrity**
26. Any resource more than one person can edit uses optimistic concurrency: a `version` field, `ETag: "<version>"` on reads/writes, `If-Match` required on PATCH/PUT/DELETE (missing → 428, stale → 412 with `currentVersion`). The repository does the check atomically (`UPDATE … WHERE id = $1 AND version = $2`). Never last-write-wins by accident.
27. State-changing actions are idempotent where natural (completing a done task → 200, no change); creation endpoints that clients may retry accept an `Idempotency-Key`.
28. Lists are always bounded (`limit` default 20, max 100). Offset + `total` is fine for small, user-sorted lists; use keyset (cursor) pagination for large or append-only data.

## Red flags — stop and fix

| You catch yourself… | Do instead |
|---|---|
| Hand-rolling a router or validator with `split('/')` and `if` chains | Use the framework's router + JSON schema / zod |
| Routing, validation, business rule and storage in one function | Split into http / use case / domain / repository |
| A use case that `import`s a concrete repository or `fastify` | Depend on the port; wire the implementation in `container.ts` |
| One big `todo.service.ts` with every action | One use-case file per action |
| `statusCode` on a domain error | `kind` on the error; map to HTTP in the error handler |
| `process.env.X` outside `config/env.ts` | Add it to `config/env.ts` |
| `throw 'msg'`, `Object.assign(new Error(), { status })` | `AppError` subclass with `code` + `statusCode` |
| Repository returns `null` to mean "duplicate" | Use case throws a domain `ConflictError` |
| `catch (e) {}` or `catch (e) { console.error(e) }` | Rethrow with `cause`, or handle and log with context |
| `app.listen()` with no signal handling | Add graceful shutdown |
| "I'm in a hurry, skip lint/types/tests" | The gate is the job. Run `npm run check`. |
| `new Date(input)` to validate a date | `format: 'date'` in the schema — JS turns `2026-02-30` into 2 March silently |
| A PATCH that overwrites whatever is stored | `version` + `If-Match` (rule 26) |
| Tests only for the happy path | One test per failure mode: 400, 404, 409, 412, 428, unknown route |

## Reference

- Reference project: `examples/todo-api/` — read its `README.md` first (tree, dependency table, request flow, "where does new code go"). Copy its layout, configs and patterns. Run: `npm install && npm run check`.
- Deeper guidance and before/after code: `references/patterns.md` (outbound HTTP, SQL repositories, optimistic concurrency, pagination, background jobs, CLI, Express projects, Fastify pitfalls).

## Done checklist

- [ ] Module folder with domain / application (ports + one file per use case) / infrastructure / http
- [ ] New instances wired only in `container.ts`; layer imports pass lint
- [ ] Config validated in one place, `.env.example` updated
- [ ] Every input schema-validated, response schemas declared
- [ ] Errors typed, central handler, consistent error body (also for unknown routes)
- [ ] Concurrent edits protected with version + If-Match
- [ ] Logs structured, secrets redacted, no `console.*`
- [ ] Graceful shutdown + timeouts on outbound I/O
- [ ] Tests for success + each failure mode, using `inject()`
- [ ] `npm run check` passes — show the output, do not claim it
