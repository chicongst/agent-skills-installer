---
name: migration-safety
description: Use when planning or reviewing a schema or data migration that runs against a live database — DDL lock impact, lock_timeout/statement_timeout, table rewrites, NOT VALID + VALIDATE constraints, concurrent index builds, batched backfills, expand–contract while old and new code run side by side, per-step rollback, monitoring, and a go/no-go call. Triggers include "is this migration safe", "zero-downtime migration", "review this migration", "backfill plan". Not for designing a schema or choosing indexes (use `db-design`) or judging a whole release beyond its migration (use `release-readiness`).
---

# Migration Safety

Review or plan a migration so that it never blocks production traffic, never breaks code that is still running, and can be rolled back at every step until an explicitly named point of no return. Engine-specific facts below are **PostgreSQL** (verified on PostgreSQL 17; version thresholds noted). MySQL differences are at the end.

## Step 0 — Establish context

Collect these before judging anything. If a fact is missing, ask the user (use AskUserQuestion if available, otherwise ask in plain text). If they cannot answer, write the assumption in the report header and plan for the worse case.

- **Engine and version** — several rules below change at PostgreSQL 11 and 12.
- **Table size and traffic** — rows, write rate, and whether long transactions run against the table (reports, exports, idle-in-transaction sessions).
- **Deploy model** — rolling, canary, or blue-green deploys mean old and new code run at the same time, and a rollback puts old code back. Assume overlap unless told otherwise.
- **Every reader and writer** of the affected columns — services, background jobs, other repositories, ETL/CDC, ad-hoc SQL. An unlisted writer is the most common cause of a broken expand–contract.
- **Migration runner** — does it wrap each file in a transaction? Can it run a statement outside one (needed for `CREATE INDEX CONCURRENTLY`)?
- **Replicas and consumers** — streaming replicas, logical replication, CDC; the replication-lag budget.
- **Recovery** — is a backup or point-in-time recovery available and tested?

## Review process

1. **Classify every statement**: lock mode, how long it is held (catalog-only, full scan, or full rewrite), and which transaction it runs in. Use the table below.
2. **Check compatibility**: for each step, can every code version that may run at that moment — old, new, and rolled-back — read and write the schema correctly?
3. **Sequence as expand → migrate → contract**, each step separately deployable and reversible.
4. **Write the rollback for each step** and name the point of no return. Once new code has written to an expanded column or table, roll back by redeploying the old code and leaving the structure in place — dropping it destroys data.
5. **Define observability and abort criteria** for each step.
6. **Decide Go / No-Go.**

## PostgreSQL lock and cost reference

`ACCESS EXCLUSIVE` blocks every read and write on the table; `SHARE` and `SHARE ROW EXCLUSIVE` block writes; `SHARE UPDATE EXCLUSIVE` blocks neither reads nor writes — it conflicts only with other schema changes, VACUUM/ANALYZE, and index builds.

| Operation | Lock | Cost | Safe form |
|---|---|---|---|
| `ADD COLUMN` nullable, or with a non-volatile `DEFAULT` (constant, `now()`), incl. `NOT NULL DEFAULT` | ACCESS EXCLUSIVE | Catalog-only (PG11+) | Fine with `lock_timeout` |
| `ADD COLUMN … NOT NULL` with no default | — | Fails on a non-empty table | Add with a default, or nullable → backfill → constraint |
| `ADD COLUMN` with a volatile default (`clock_timestamp()`, `gen_random_uuid()`) or a `STORED` generated column | ACCESS EXCLUSIVE | Full table rewrite | Add nullable → `SET DEFAULT` (no rewrite; covers new rows) → backfill existing rows in batches |
| `ALTER COLUMN … TYPE` | ACCESS EXCLUSIVE | Rewrite + index rebuild, except binary-coercible changes (`varchar(n)` → longer `varchar` or `text`) | New column + backfill + switch reads |
| `RENAME COLUMN` / `RENAME TABLE` | ACCESS EXCLUSIVE | Catalog-only | The danger is running code using the old name → expand–contract |
| `DROP COLUMN` | ACCESS EXCLUSIVE | Catalog-only | Only after no running code references it |
| `SET NOT NULL` | ACCESS EXCLUSIVE | Full scan under the lock, skipped if a validated `CHECK (col IS NOT NULL)` exists (PG12+) | `CHECK … NOT VALID` → `VALIDATE` → `SET NOT NULL` → drop the CHECK |
| `ADD CONSTRAINT … CHECK` | ACCESS EXCLUSIVE | Full scan under the lock | `NOT VALID` (brief), then `VALIDATE CONSTRAINT` (SHARE UPDATE EXCLUSIVE, scans) |
| `ADD FOREIGN KEY` | SHARE ROW EXCLUSIVE on both tables | Full scan under the lock | `NOT VALID`, then `VALIDATE` (SHARE UPDATE EXCLUSIVE; ROW SHARE on the referenced table) |
| `CREATE INDEX` | SHARE | Full build with writes blocked | `CREATE INDEX CONCURRENTLY` (Rule 3) |
| `ADD UNIQUE` / `PRIMARY KEY` | ACCESS EXCLUSIVE | Index build under the lock | `CREATE UNIQUE INDEX CONCURRENTLY`, then `ADD CONSTRAINT … UNIQUE USING INDEX` (brief) |
| `DROP INDEX` | ACCESS EXCLUSIVE | Brief | `DROP INDEX CONCURRENTLY` |
| `CREATE TRIGGER` / `DROP TRIGGER` | SHARE ROW EXCLUSIVE / ACCESS EXCLUSIVE | Brief | Fine with `lock_timeout` |

## Rules

1. **Every DDL sets `lock_timeout`.** A statement waiting for ACCESS EXCLUSIVE behind one long transaction blocks every later query on the table — including plain SELECTs — for as long as it waits. Set it to a few seconds (`SET LOCAL` inside the runner's transaction) and retry with backoff. Add a short `statement_timeout` to catalog-only DDL; raise or disable it for scans (`VALIDATE`, backfills) and say why.
2. **Locks are held until commit.** One ACCESS EXCLUSIVE statement at the top of a file that then runs a backfill or a validation keeps the whole table blocked for all of it. Put catalog DDL, backfills, `VALIDATE`, and concurrent index builds in separate migrations.
3. **Build indexes concurrently.** `CREATE INDEX CONCURRENTLY` takes SHARE UPDATE EXCLUSIVE, must run outside a transaction block (use the runner's non-transactional mode), and waits for transactions that started before it. Don't give it a short `lock_timeout`: its wait blocks no reads or writes, and a timeout discards the build. Any failure (duplicate key, cancel, timeout) leaves an **INVALID** index that still slows writes — find it with `SELECT indexrelid::regclass FROM pg_index WHERE NOT indisvalid;`, `DROP INDEX CONCURRENTLY`, retry. Progress: `pg_stat_progress_create_index`.
4. **Add constraints `NOT VALID`, validate in a separate transaction.** `NOT VALID` still checks every new INSERT and UPDATE, including updates to old rows that violate it. Add it only after every writer complies and the backfill has finished.
5. **Backfill in batches, outside the migration transaction.** Walk the primary key in ranges, commit each batch, sleep between batches, keep it idempotent (`WHERE new_col IS NULL`) and resumable (log the last range). Capture `max(id)` at the start; rows inserted later must be covered by the trigger or dual-write. PostgreSQL has no `UPDATE/DELETE … LIMIT`; use PK ranges (or `WHERE ctid IN (SELECT ctid … LIMIT n)`). One batch:

   ```sql
   UPDATE orders
      SET amount_cents = amount * 100
    WHERE id >= :lo AND id < :lo + :batch_size
      AND amount_cents IS NULL;
   ```

   A PL/pgSQL procedure can loop and `COMMIT` per batch only when `CALL`ed outside a transaction block, and `statement_timeout` then applies to the whole `CALL`, while `lock_timeout` still applies to each lock wait.
6. **Cover every write path during expand–contract.** Any writer still producing the old shape leaves rows the backfill already passed, and the later NOT NULL fails or starts rejecting that writer. Choose one:
   - **Database trigger** (default when writers span repos, jobs, or ad-hoc SQL): fires for every INSERT/UPDATE, including `COPY`; it does not fire for `TRUNCATE` or in sessions with `session_replication_role = replica`. Test that it handles each write shape (old-code write, new-code write, backfill update) and that the backfill's updates do not rewrite the source column. Drop it in the same transaction that drops the old column.
   - **Dual-write in application code**: only when you can list every writer and show each one is updated.
7. **Contract last.** Drop old columns and tables only after the new code has baked and you have evidence nothing reads them (grep every repo, check jobs, check `pg_stat_statements` if installed). That step is the point of no return; keep an archive copy or confirmed point-in-time recovery.
8. **No invented numbers.** Durations and thresholds come from the input, a staging run on production-sized data, or timing the first batches — otherwise label them "estimate" or "assumption".
9. **Plan and review; don't execute.** Never run DDL or backfills against a shared or production database without the user's explicit go-ahead for that environment.

## MySQL differences (InnoDB, 8.0+)

- DDL is not transactional: each statement commits implicitly, so a failed multi-statement migration leaves partial state. One DDL per migration.
- State `ALGORITHM=INSTANT` or `ALGORITHM=INPLACE, LOCK=NONE` explicitly; the statement then errors instead of silently falling back to a blocking table copy.
- Metadata-lock waits queue like PostgreSQL's; `lock_wait_timeout` defaults to one year — set it to a few seconds in the migration session.
- For changes that need a table copy on a large table, use an online schema-change tool (gh-ost, pt-online-schema-change).

## Severity

- **🔴 BLOCKER** — causes an outage, data loss or corruption, or errors in running code (long ACCESS EXCLUSIVE on a hot table, dropping a column still in use, a constraint a live writer violates).
- **🟠 MAJOR** — real risk under realistic conditions (no `lock_timeout`, unbatched backfill, a step with no rollback, silently wrong data transformation).
- **🟡 MINOR** — robustness or observability gap.
- **💭 NIT** — style; mention briefly.

## Output format

A worked example is in `examples/example.txt` (if installed). `template.md` mirrors this format.

```markdown
# Migration Safety Review: [Migration name]

**Engine**: [e.g., PostgreSQL 17 — or "assumed: …"]
**Scale & traffic**: [rows, write rate, replicas — from input, or "unknown"]
**Deploy model**: [rolling / blue-green / downtime window; do old and new code overlap?]

## Change Summary
[What changes, in plain language, and which code/jobs are affected]

## Findings
### [🔴 BLOCKER / 🟠 MAJOR / 🟡 MINOR / 💭 NIT] [Title]
**Where**: [file:line or the statement]
**Problem**: [lock/rewrite/compatibility failure and its consequence]
**Fix**: [the safe replacement]

## Risk Assessment
| Risk | Severity | Likelihood | Mitigation |
|------|----------|------------|------------|

## Safe Execution Sequence
### Step N — [EXPAND / MIGRATE / DEPLOY / CONTRACT]: [what]
- **Runs as**: [migration (transactional) / non-transactional migration / background job / app deploy]
- **Lock**: [mode and how long it is held]
- **Change**: [SQL or code change]
- **Duration**: [measured, estimated with basis, or "measure on first batches"]
- **Monitor**: [queries/dashboards]
- **Abort if**: [threshold]
- **Rollback**: [exact commands]

## Compatibility Matrix
| Code version | [Schema state A] | [Schema state B] | Compatible? |
|--------------|------------------|------------------|-------------|

## Rollback Plan
**Trigger**: [conditions that require rollback]
**Point of no return**: [the step after which rollback means restore]
| Step | Rollback | Data impact |
|------|----------|-------------|

## Observability
[What to watch during and after, with queries]

## Validation Queries
[Queries that prove the migration is correct]

## Go / No-Go
**[GO / GO WITH CONDITIONS / NO-GO]** — [one sentence]
- [ ] [Precondition, e.g., rehearsed on production-sized data including rollback]
```

Omit **Findings** when planning from scratch with no proposed migration to review. Verdicts (same scale as `release-readiness`): **GO** — no BLOCKER or MAJOR open. **GO WITH CONDITIONS** — no BLOCKER; each open MAJOR or checklist item has an owner and a deadline before the migration starts, and is re-checked then. **NO-GO** — any BLOCKER (an unknown writer or deploy model counts as one until answered); list what would flip the verdict.
