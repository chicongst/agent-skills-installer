# Node.js Patterns — before / after

Each pattern lists the rule it serves. Code is TypeScript (erasable syntax), Node ≥ 22.18.

## 1. Outbound HTTP: timeout, typed failure, cause chain (rules 10, 15)

```ts
// ❌ Hangs forever if the partner API stalls; error loses status and body
const res = await fetch(url);
const data = await res.json();
```

```ts
// ✅
import { AppError } from '../shared/errors/app-error.ts';

// Add 'upstream' to ErrorKind and `upstream: 502` to STATUS_BY_KIND in shared/http/error-handler.ts
export class UpstreamError extends AppError {
  readonly kind = 'upstream';
  readonly code = 'UPSTREAM_FAILED';
}

export async function fetchJson<T>(url: string, { timeoutMs = 5_000 } = {}): Promise<T> {
  let res: Response;
  try {
    res = await fetch(url, { signal: AbortSignal.timeout(timeoutMs) });
  } catch (cause) {
    throw new UpstreamError(`Request to ${new URL(url).host} failed`, { cause });
  }
  if (!res.ok) {
    throw new UpstreamError(`Upstream responded ${String(res.status)}`, {
      details: { status: res.status, host: new URL(url).host },
    });
  }
  return (await res.json()) as T;
}
```

Retry only idempotent calls (GET, PUT with the same body, POST with an idempotency key), with capped exponential backoff + jitter, and never retry 4xx except 408/429.

## 2. SQL repository: parameters, pagination, transactions (rules 2, 18)

```ts
// ❌ SQL injection, unbounded result set
pool.query(`SELECT * FROM customers WHERE name LIKE '%${q}%'`);
```

```ts
// ✅ pg — placeholders, explicit columns, keyset pagination, bounded limit
import type { Pool } from 'pg';
import type { Customer } from './customer.schema.ts';

const MAX_PAGE_SIZE = 100;

export class PgCustomerRepository {
  readonly #pool: Pool;
  constructor(pool: Pool) {
    this.#pool = pool;
  }

  async list({ after, limit = 20 }: { after?: string; limit?: number }): Promise<Customer[]> {
    const size = Math.min(Math.max(limit, 1), MAX_PAGE_SIZE);
    const { rows } = await this.#pool.query<Customer>(
      `SELECT id, name, email, created_at AS "createdAt"
         FROM customers
        WHERE ($1::uuid IS NULL OR id > $1)
        ORDER BY id
        LIMIT $2`,
      [after ?? null, size],
    );
    return rows;
  }

  async transferSites(fromId: string, toId: string): Promise<void> {
    const client = await this.#pool.connect();
    try {
      await client.query('BEGIN');
      await client.query('UPDATE sites SET customer_id = $2 WHERE customer_id = $1', [fromId, toId]);
      await client.query('UPDATE customers SET merged_into = $2 WHERE id = $1', [fromId, toId]);
      await client.query('COMMIT');
    } catch (err) {
      await client.query('ROLLBACK');
      throw err;
    } finally {
      client.release();
    }
  }
}
```

Unique constraints belong in the database; map the driver's duplicate error (`err.code === '23505'` in Postgres) to `ConflictError` inside the repository so the service stays storage-agnostic.

## 3. Streams: always `pipeline` (rule 16)

```ts
// ❌ Leaks file handles on error, no backpressure handling
fs.createReadStream(src).pipe(zlib.createGzip()).pipe(fs.createWriteStream(dst));
```

```ts
// ✅
import { createReadStream, createWriteStream } from 'node:fs';
import { pipeline } from 'node:stream/promises';
import { createGzip } from 'node:zlib';

await pipeline(createReadStream(src), createGzip(), createWriteStream(dst));
```

## 4. Background job / webhook consumer: idempotent (rules 11, 14)

```ts
export async function handleJobCompleted(event: { id: string; jobId: string }, deps: Deps): Promise<void> {
  const firstTime = await deps.processedEvents.markIfNew(event.id);
  if (!firstTime) {
    deps.log.info({ eventId: event.id }, 'duplicate event skipped');
    return;
  }
  await deps.sentinel.updateJobStatus(event.jobId, 'completed');
}
```

Every message may arrive twice. Store the event id with a unique constraint and process inside the same transaction when possible.

## 5. Concurrency: bounded, not `Promise.all` over unbounded input (rule 15)

```ts
// ❌ 10 000 customers → 10 000 simultaneous requests
await Promise.all(customers.map((c) => syncCustomer(c)));
```

```ts
// ✅ Fixed-size worker pool, no dependency
export async function mapLimit<T, R>(items: readonly T[], limit: number, fn: (item: T) => Promise<R>): Promise<R[]> {
  const results = new Array<R>(items.length);
  let next = 0;
  async function worker(): Promise<void> {
    while (next < items.length) {
      const index = next++;
      results[index] = await fn(items[index] as T);
    }
  }
  await Promise.all(Array.from({ length: Math.min(limit, items.length) }, worker));
  return results;
}
```

## 6. CLI scripts: `node:util` parseArgs, exit codes (rules 8, 13)

```ts
import { parseArgs } from 'node:util';

const { values } = parseArgs({
  options: {
    file: { type: 'string', short: 'f' },
    'dry-run': { type: 'boolean', default: false },
  },
  strict: true,
});

if (!values.file) {
  process.stderr.write('Usage: import-customers --file <path> [--dry-run]\n');
  process.exit(2);
}
```

Exit 0 on success, 1 on runtime failure, 2 on bad usage. Write data to stdout, diagnostics to stderr.

## 7. Express projects (when the repo already uses Express)

Same module layout (`domain/`, `application/`, `infrastructure/`, `http/`) and the same `container.ts`; only `app.ts`, `http/*.routes.ts` and the error middleware change. Express 5 forwards rejected promises from async handlers to the error middleware.

```ts
import express, { type ErrorRequestHandler } from 'express';

export function buildApp(container: Container) {
  const app = express();
  app.disable('x-powered-by');
  app.use(express.json({ limit: '1mb' }));
  app.use('/todos', todoRouter(container.todos));

  const errorHandler: ErrorRequestHandler = (err, req, res, _next) => {
    if (err instanceof AppError) {
      res.status(STATUS_BY_KIND[err.kind]).json({ error: { code: err.code, message: err.message } });
      return;
    }
    req.log.error({ err }, 'unhandled error');
    res.status(500).json({ error: { code: 'INTERNAL_ERROR', message: 'Internal server error' } });
  };
  app.use(errorHandler);
  return app;
}
```

Add `helmet`, `express-rate-limit`, and a schema validator (zod) — Express ships none of them. Test with `supertest(buildApp(createContainer(testConfig)))`.

## 8. Choosing libraries

| Need | Default | Why |
|---|---|---|
| HTTP framework | Fastify (new project), keep Express/Nest if the repo uses it | Schema validation + serialization + pino built in |
| Validation outside HTTP | zod | Types inferred from the schema |
| Logging | pino | Fast JSON logs, redaction, child loggers |
| HTTP client | built-in `fetch` (undici) | No dependency; `AbortSignal.timeout` |
| Postgres | `pg` + SQL, or Prisma/Drizzle if the team wants an ORM | Parameterized by default |
| Tests | `node:test`, or Vitest if the repo uses it | Zero-dependency, built into Node |
| Env files | `node --env-file-if-exists=.env` | No `dotenv` needed on Node ≥ 22 |

Before adding a dependency: check weekly downloads, last release, open security advisories (`npm audit`), and whether Node already does it.

## 9. Optimistic concurrency: version + ETag + If-Match (rule 26)

Full working version: `examples/todo-api/` — `application/use-cases/update-todo.ts`, `application/versioned-write.ts`, `infrastructure/postgres-todo.repository.ts`, `src/shared/http/etag.ts`.

```ts
// ❌ Two people edit the same record; the slower save silently wins
await db.query('UPDATE customers SET name = $2 WHERE id = $1', [id, name]);
```

```ts
// ✅ The write only happens if nobody changed the row since the client read it
const { rowCount } = await pool.query(
  `UPDATE customers
      SET name = $3, version = version + 1, updated_at = now()
    WHERE id = $1 AND version = $2`,
  [id, expectedVersion, name],
);
if (rowCount === 0) {
  const exists = await pool.query('SELECT version FROM customers WHERE id = $1', [id]);
  return exists.rowCount === 0 ? 'not_found' : 'version_mismatch';
}
return 'replaced';
```

HTTP contract: `GET` returns `ETag: "3"`; client sends `If-Match: "3"`; missing header → 428, stale → 412 `{ error: { code: 'VERSION_MISMATCH', details: { currentVersion } } }`. Parse the header in the route (HTTP concern), pass a plain `expectedVersion: number` to the service.

## 10. Fastify pitfalls

| Pitfall | Symptom | Fix |
|---|---|---|
| Default Ajv `coerceTypes` applies to bodies | `{ "name": 123 }` stored as `"123"` | Separate body compiler with `coerceTypes: false` (`src/shared/http/validator-compiler.ts`); keep coercion for query/params |
| Default `removeAdditional` | Unknown fields silently dropped; `minProperties: 1` passes for `{ "status": "done" }` then becomes an empty no-op that still bumps the version | `removeAdditional: false` for bodies → 400 |
| `anyOf: [{type:'string'},{type:'null'}]` + coercion | `null` turns into `""` | `type: ['string', 'null']` |
| `content-type: application/json` with empty body | `FST_ERR_CTP_EMPTY_JSON_BODY` 400 on action endpoints like `POST /todos/:id/complete` | Document "send no body and no content-type", or register a parser that maps empty → `{}` |
| No `setNotFoundHandler` | Unknown routes return Fastify's own `{ message, error, statusCode }` shape | Register one that uses the standard error body |
| Framework `FST_*` codes leaking to clients | Clients couple to internals | Map 4xx framework errors to `http.STATUS_CODES` names (`BAD_REQUEST`, `PAYLOAD_TOO_LARGE`) |
| Missing `await app.register(...)` / `done()` | Routes missing or plugin hangs | Async plugin → `await register`; callback plugin → call `done()` |

## 11. Pagination choices (rule 28)

| Case | Use | Response |
|---|---|---|
| Small per-user lists, user-chosen sort | `limit` + `offset` | `{ items, total, limit, offset }` |
| Large tables, feeds, sync jobs | Keyset on `(sortField, id)` | `{ items, nextCursor }` — cursor = base64 of last `(sortField, id)` |
| Sorting on a nullable field | Put nulls last explicitly (`NULLS LAST`) and tie-break on `id` | — |

Never return an unbounded list. Cap `limit` in the schema (`maximum: 100`), not only in code.
