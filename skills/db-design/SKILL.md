---
name: db-design
description: Use when designing or reviewing a relational database schema — modeling entities, choosing types, keys and constraints, enforcing multi-tenant isolation, deriving indexes from known queries, or defining the target schema of a change. PostgreSQL by default. Not for executing or reviewing a migration rollout (locks, backfills, rollback) — use `migration-safety`; not for diagnosing slow queries or latency in a running system — use `performance-review`; not for service boundaries or data flow between systems — use `architect`.
---

# Database Design

Act as a senior database designer: constraints enforce the business rules, every index is derived from a stated query, and both are proven by running them when possible.

## Step 0 — Inputs before design

1. **Engine and version.** Default to PostgreSQL 13+ and say so; do not transfer PostgreSQL facts to other engines silently.
2. **Existing schema.** Read migrations / ORM models first and follow their conventions (naming, key type, timestamps, soft delete).
3. **Access patterns.** Top queries (filters, sort, page size), read/write mix, row counts, tenancy, retention/erasure rules.

If a missing answer would change the design, ask the user (use AskUserQuestion if available, otherwise ask in plain text); otherwise proceed and list it under **Assumptions**. Never invent row counts, QPS or latencies — a number that drives a decision comes from the input or is labeled an assumption.

## Workflow

1. **Domain model** — entities, cardinality, lifecycle, and *who owns each row*.
2. **Tables, types, constraints** — apply the rules below; list any business rule left to the application and why.
3. **Queries → indexes** — write each key query in SQL, then design the index that serves it. No query, no index (except FK-support indexes).
4. **Verify** — run the DDL and queries on a real engine when possible (e.g. `docker run -d --rm --name pg -e POSTGRES_PASSWORD=pw postgres:17`, then `docker exec -i pg psql -U postgres …`), seed synthetic data sized to the stated volumes, and `EXPLAIN (ANALYZE)` each query. Report the plan node seen as `[verified]`; anything not run is `[unverified]`. Tiny tables get sequential scans — seed enough rows before judging an index.
5. **Evolution** — for changes to an existing schema, see Schema evolution below.

## Types and keys

- **Primary keys**: `bigint GENERATED ALWAYS AS IDENTITY` for internal rows; `uuid` when IDs are generated outside the DB, exposed publicly and must not be guessable, or merged across databases. Random UUIDv4 keys scatter btree inserts; UUIDv7 is time-ordered (`uuidv7()` built in from PostgreSQL 18; generate it in the app on older versions).
- **Time**: `timestamptz` for instants, `date` for calendar dates. **Money**: `numeric(p,s)` or integer minor units plus currency — never floating point.
- **Strings**: in PostgreSQL `text` and `varchar(n)` perform the same; use `text` plus a `CHECK` when a real length rule exists. Case-insensitive uniqueness needs a unique index on `lower(col)` (or `citext`).
- **Enumerations**: `text` + `CHECK (col IN (...))` or a lookup table with FK. Native `ENUM` types can add values but cannot drop one (PostgreSQL: "dropping an enum value is not implemented").
- **JSONB** only for sparse/schemaless attributes; anything filtered, joined or constrained gets a column. **NOT NULL** by default.

## Constraints

- **Every reference gets an FK.** PostgreSQL does not index the referencing column; index it unless an existing index already leads with it — parent `DELETE`/`UPDATE` checks and joins from the parent otherwise scan the child.
- **Choose `ON DELETE` per relationship**: `CASCADE` for owned children (task → its assignments), `RESTRICT`/`NO ACTION` for references to independent entities (task → creator).
- **Uniqueness**: natural keys stay `UNIQUE` even with a surrogate PK; every junction table has a PK or `UNIQUE` on the pair. With soft delete, use a partial unique index `... WHERE deleted_at IS NULL`.
- **`CHECK`** for ranges and states. Replace boolean-flag combinations (`is_active`, `is_banned`) with one `status` column.
- **Cross-row rules**: exclusion constraints, e.g. no overlapping bookings: `EXCLUDE USING gist (room_id WITH =, during WITH &&)` (needs the `btree_gist` extension for the `=` on a scalar column).

## Multi-tenant isolation

A `tenant_id` column alone does not isolate anything. Enforce both layers when the input says tenants must be isolated:

1. **Referential** — every tenant-owned table carries `org_id`; each parent exposes `UNIQUE (org_id, id)`; every FK between tenant tables is composite: `FOREIGN KEY (org_id, project_id) REFERENCES projects (org_id, id)`. The database then rejects a row that links to another tenant's data.
2. **Read/write** — row-level security: `ENABLE ROW LEVEL SECURITY` plus `CREATE POLICY ... USING (org_id = <current tenant>)`, with the tenant set per transaction (`SET LOCAL app.org_id = ...`). Write the setting read as `NULLIF(current_setting('app.org_id', true), '')::uuid` — after a `SET LOCAL` ends the value reverts to `''`, not NULL. Table owners bypass RLS unless `FORCE ROW LEVEL SECURITY`; superusers and `BYPASSRLS` roles always bypass — the app must connect as a non-owner role. Global tables that tenants read (users, organizations) need a policy too, e.g. users visible only when they are members of the current org, with a narrow `SECURITY DEFINER` function for lookups that run before a tenant is set (login).

Lead indexes that serve tenant queries with `org_id`. Schema-per-tenant or database-per-tenant are alternatives; state why you rejected them.

## Indexing

- **Equality columns first, then the range/sort column**. `(a, b, c)` can seek on `a`, `a,b`, `a,b,c`, and serve `WHERE a = ? ORDER BY b`. A query on `b` alone cannot seek; it may scan the whole index (PostgreSQL 18's skip scan makes this cheap only when `a` has few distinct values).
- **Direction**: a btree is scanned in either direction, so `(created_at)` serves `ORDER BY created_at DESC`. Only mixed directions (`ORDER BY a, b DESC`) need a matching `(a, b DESC)` index (or its exact reverse `(a DESC, b)`) to avoid a sort.
- **LIMIT** stops early only when an index delivers rows already filtered and in order; otherwise every matching row is read and sorted first (the plan shows a `Sort` with `top-N heapsort` under the `Limit`).
- **Pagination**: keyset with a unique tie-breaker — `WHERE (created_at, id) < ($1, $2) ORDER BY created_at DESC, id DESC LIMIT 50` on an index ending in `(created_at, id)`. `OFFSET n` reads and discards `n` rows.
- **Low-selectivity columns** (`status`, booleans) are rarely useful alone; use them as an equality column inside a composite, or as a partial-index predicate (`WHERE status = 'open'`).
- **Partial and expression indexes** are used only when the query repeats the predicate/expression: an index on `lower(email)` does nothing for `WHERE email = $1`; `WHERE created_at::date = $1` cannot use an index on `created_at` — rewrite as a range.
- **Covering**: `INCLUDE (cols)` enables index-only scans for hot reads; they stay cheap only while vacuum keeps the visibility map current.
- **Joins**: without an index on the join column PostgreSQL hash- or merge-joins; FK indexes pay off for per-parent lookups and parent deletes.
- **Cost**: every index slows writes and blocks HOT updates when its columns change. Find unused ones via `pg_stat_user_indexes.idx_scan = 0` over a representative window (stats are per node — check replicas too).

## Only when requirements justify

- **Partitioning** — for retention or queries that always filter on the key; every PK/unique must include the key.
- **Materialized views** — for repeated aggregates that may be stale; `REFRESH … CONCURRENTLY` needs a unique index on the view.
- **Denormalized copies/counters** — name the source of truth and how drift is corrected.

## Anti-patterns

| Anti-pattern | Fix |
|---|---|
| `entity_type` + `entity_id` polymorphic reference (no FK possible) | One FK column per target, or one junction table per target |
| Comma-separated values in a column | Junction table |
| EAV `(entity, key, value)` for core attributes | Real columns; JSONB for the truly dynamic remainder |
| Natural key (email) as PK | Surrogate PK + `UNIQUE` on the natural key |
| Column type differs from the values compared to it | Store the right type; PostgreSQL rejects `varchar = integer`, MySQL casts the column and skips its index |

## Schema evolution (design side only)

For a live schema, give the target schema and an expand/contract path: add structures compatibly → backfill in batches → add constraints `NOT VALID`, then `VALIDATE CONSTRAINT` → switch reads/writes → drop the old structure in a later release; index existing tables with `CREATE INDEX CONCURRENTLY`. Lock levels, timeouts, batch sizing and rollback belong to `migration-safety`.

## Reviewing an existing schema

Run the same checks against the given DDL and report each defect under **Findings** with the shared severities: 🔴 BLOCKER — must fix before release (data loss/corruption, cross-tenant leak, broken invariant); 🟠 MAJOR — real defect that will bite soon (missing constraint or FK index, wrong type, key query with no usable index); 🟡 MINOR — maintainability, naming; 💭 NIT — style. Cite `table.column` or the DDL line and give the corrected DDL.

## Output format

A worked example is in `examples/example.txt` (if installed). `template.md` mirrors this format.

````markdown
# Database Design: [System / feature]

**Engine**: [e.g. PostgreSQL 17] · **Scope**: [new schema / change to existing schema / review]

## Findings
- [🔴/🟠/🟡/💭] **[table.column or DDL line]** — [defect] → [corrected DDL]

## Assumptions
- [Assumption not stated in the input — confirm with user]

## Domain Model
- [Entity] 1:N [Entity] — [ownership / lifecycle note]

## Schema
### [table]
| Column | Type | Constraints | Notes |
|---|---|---|---|
| [col] | [type] | [PK / FK → / NOT NULL / CHECK / UNIQUE] | [why] |

**Table constraints**: [composite UNIQUE / FK / CHECK / EXCLUDE]

## DDL
```sql
[Complete, runnable DDL: tables, indexes, policies]
```

## Indexes
| Index | Definition | Serves | Notes |
|---|---|---|---|
| [name] | [(cols) / WHERE / INCLUDE] | [Q# or FK] | [trade-off] |

## Query Patterns
### Q1 — [purpose]
```sql
[query with explicit columns and $n parameters]
```
**Plan**: [verified — plan node seen, engine, data size] or [unverified — expected plan]

## Data Integrity
| Business rule | Enforced by |
|---|---|
| [rule] | [constraint / policy / application — why] |

## Migration Strategy
[New schema: how it is created. Change: expand/contract steps. Rollout details → `migration-safety`.]

## Trade-offs & Open Questions
- **[Decision]** — [alternative considered, why rejected, what would change it]
- [Open question for the user]
````

If nothing could be run, every `**Plan**` line reads `[unverified — expected ...]`; never imply a plan was measured. Include **Findings** only for reviews, and there limit Schema/DDL to the tables you change. Omit Assumptions or Open Questions only when there are none.
