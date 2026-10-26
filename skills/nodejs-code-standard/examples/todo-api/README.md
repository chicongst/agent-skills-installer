# Todo API — reference structure

Fastify 5 + TypeScript (run directly by Node) + `node:test`. In-memory or Postgres storage, picked by `STORAGE_DRIVER`.

```bash
npm install
npm run check            # typecheck + lint + tests
npm run dev              # http://127.0.0.1:3000
```

## Folder structure

```
src/
├── main.ts                         # entry: config → container → app → listen → signals
├── app.ts                          # builds the Fastify instance (no listen) — tests use this
├── container.ts                    # composition root: the ONLY place that calls `new` on infra
├── config/
│   └── env.ts                      # the ONLY reader of process.env; validated + frozen
├── shared/                         # cross-module building blocks, no business rules
│   ├── errors/app-error.ts         # AppError + kinds (validation, not_found, conflict, …)
│   ├── http/                       # error handler, error body schema, ETag, validator
│   ├── lifecycle/process-handlers.ts
│   ├── database/postgres-pool.ts
│   ├── time/clock.ts               # Clock port + systemClock
│   ├── ids/id-generator.ts
│   └── pagination/page.ts
└── modules/
    └── todos/                      # one folder per business module
        ├── todo.module.ts          # wires the module's use cases from its deps
        ├── domain/                 # pure rules: no I/O, no framework, no async
        │   ├── todo.ts             # entity + createTodo / applyChanges / markDone / reopen
        │   └── todo.errors.ts
        ├── application/            # use cases: orchestrate domain + ports
        │   ├── ports/todo.repository.ts   # interface the use cases need
        │   ├── use-cases/          # one file = one action
        │   │   ├── create-todo.ts
        │   │   ├── get-todo.ts
        │   │   ├── list-todos.ts
        │   │   ├── update-todo.ts
        │   │   ├── complete-todo.ts
        │   │   ├── reopen-todo.ts
        │   │   └── delete-todo.ts
        │   └── versioned-write.ts  # shared optimistic-concurrency steps
        ├── infrastructure/         # implementations of the ports
        │   ├── in-memory-todo.repository.ts
        │   └── postgres-todo.repository.ts
        └── http/                   # transport only
            ├── todo.routes.ts
            └── todo.schemas.ts
migrations/001_create_todos.sql
test/
├── helpers/                        # buildTestApp, fixedClock
├── unit/modules/todos/{domain,application}/   # mirrors src/
└── integration/todos/todos.http.test.ts       # through HTTP with app.inject()
```

## Dependency rule

```
http ──▶ application ──▶ domain
             ▲
infrastructure (implements application/ports)

container.ts wires everything; nothing imports container.ts except main.ts and test helpers.
```

| Layer | May import | Must not import | Enforced by |
|---|---|---|---|
| `domain/` | `shared/errors` | application, infrastructure, http, `fastify`, `pg` | ESLint `no-restricted-imports` |
| `application/` | domain, own `ports/`, `shared/{time,ids,pagination,errors}` | infrastructure, http, `fastify`, `pg` | ESLint `no-restricted-imports` |
| `infrastructure/` | domain, application ports, drivers (`pg`) | http | review |
| `http/` | application use cases, domain types, `shared/http` | infrastructure | review |

## How instances are created

- `container.ts` creates **one instance of each thing per container**: clock, id generator, repository (and its pool), then every use case via `createTodoUseCases`.
- Use cases receive dependencies through the constructor (`new UpdateTodo({ todos, clock })`); they never `import` a concrete repository.
- Each test calls `buildTestApp()` → a **fresh container** → isolated state; overrides (`fixedClock()`, fake repository) are passed in, not monkey-patched.
- Resources with a lifetime (Postgres pool) are released by `container.close()`, called on shutdown and in the test app's `onClose` hook.

## Request flow — `PATCH /todos/:id`

1. `todo.schemas.ts` validates params, body (strict: no coercion, unknown fields → 400) and declares the response shape.
2. `todo.routes.ts` parses `If-Match` → `expectedVersion`, calls `useCases.update.execute(...)`.
3. `UpdateTodo` loads the todo, checks the version, calls the pure `applyChanges`, writes with `todos.update(next, expectedVersion)`.
4. The repository writes only if the stored version still matches (`UPDATE … WHERE id = $1 AND version = $2`).
5. Errors are domain errors (`TodoVersionMismatchError`); `shared/http/error-handler.ts` maps their `kind` to 412.

## Where does new code go?

| You are adding… | Put it in |
|---|---|
| A business rule ("can't complete a todo with no title") | `domain/todo.ts` as a pure function + unit test |
| A new action ("archive todo") | `application/use-cases/archive-todo.ts`, register in `todo.module.ts`, route in `http/` |
| A new storage backend | `infrastructure/<name>-todo.repository.ts` implementing the port; select it in `container.ts` |
| A new env variable | `config/env.ts` + `.env.example` |
| A new module ("projects") | copy the `modules/todos/` shape; wire it in `container.ts` and `app.ts` |
| Something two modules need | `shared/` — only if it has no business meaning |
