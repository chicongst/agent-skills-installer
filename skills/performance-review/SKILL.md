---
name: performance-review
description: Use when an endpoint, query, job, page, or service is slow and you need the bottleneck found from measurements (percentiles, traces, profiles, EXPLAIN ANALYZE), fixes ranked by gain, cost, and rollout risk, and a re-measurement plan; also to review a load test. Triggers: "why is this slow", "p99", "review hiệu năng", "tối ưu hiệu năng". Not for code-level complexity review (use `algorithm-review`), schema/index design (use `db-design`), applying DB changes safely (use `migration-safety`), or a live incident (use `sre-engineering`).
---

# Performance Review

Find where the time actually goes, fix the biggest measured cost first, say what each fix costs and risks, and prove the gain by re-measuring.

## Step 0 — Baseline and target before anything else

Collect, from the input or by asking (use AskUserQuestion if available, otherwise ask in plain text):

- **What is slow, for whom**: the user-facing operation, its call rate, and whether it is on the critical path.
- **Latency percentiles** (p50/p95/p99, plus max if available) with source and window (APM, logs, load test, EXPLAIN). An average alone is not a baseline.
- **Target**: an SLO or budget. If none is stated, write "not stated", propose one, and ask. Without a target you cannot say when to stop.
- **Environment**: prod or a copy? Same data size and distribution, same version, same hardware class? Warm or cold cache? What concurrency?

If there are no measurements, do not produce numbers. Output a measurement plan and label every suspected cause as a **hypothesis**.

## Workflow (in order)

1. **Baseline**: record percentiles under representative load, with the tool and window you will reuse in step 5.
2. **Profile**: break the time down by phase (network, queue/pool wait, app CPU, DB, downstream calls, serialization). Use a trace or profile, not intuition.
3. **Hypothesis**: name the one mechanism behind the largest share and the evidence for it (plan node, flame-graph frame, span).
4. **Change**: one change at a time, smallest one that tests the hypothesis.
5. **Re-measure**: repeat the baseline exactly. Keep the change only if the target percentile moved beyond run-to-run noise. Stop when the target is met.

## Measurement rules

- **Percentiles, not averages.** Report p50/p95/p99. Percentiles cannot be averaged across hosts or time windows; recompute them from raw data or histograms.
- **Explain the gap.** If a lab measurement (e.g., warm staging EXPLAIN) is much faster than production p99, the bottleneck is not proven. List the candidates (cold cache, other inputs, concurrency, pool wait, lock waits, GC) and how to capture each.
- **Representative inputs.** Latency often depends on the input: broad vs rare search terms, big vs small tenants, skewed values. Measure each class, not one convenient case.
- **Representative load.** Production-sized data, production-like concurrency, and a request mix taken from real traffic. Use a constant-arrival-rate (open-model) load generator, such as wrk2 or k6 `constant-arrival-rate`. Closed-loop tools that wait for each response before sending the next (coordinated omission) under-report tail latency.
- **Repeat and report spread.** Run at least 3 times. Report min–max or all runs, and whether the cache was warm.
- **Latency vs throughput.** Say which one is the problem. At steady state, concurrency = throughput × latency (Little's law). Use it to check pool and worker sizing.

## Profiling by layer (examples; use what the stack already has)

| Layer | Tools |
|---|---|
| PostgreSQL | `EXPLAIN (ANALYZE, BUFFERS)`, `pg_stat_statements` (mean/stddev/max per query, not percentiles), `auto_explain` for slow plans in production |
| App CPU/alloc | Sampling profilers and flame graphs: py-spy, async-profiler, pprof, dotnet-trace, 0x/clinic |
| Request path | Distributed traces/APM spans; include pool-wait and queue-wait spans |
| Browser | Field Core Web Vitals (RUM) first; Lighthouse is a lab signal |

Reading `EXPLAIN ANALYZE` (PostgreSQL):
- It **executes** the statement. Wrap data-modifying statements in `BEGIN; … ROLLBACK;`.
- Node `actual time` is per loop. Multiply by `loops` for the total, and subtract child times to get a node's own cost.
- Compare estimated `rows` with actual `rows`. A 10×+ gap means the planner is choosing blind. Find out why (a join on a lookup value, stale stats, correlated columns) before adding indexes.
- `Buffers: shared hit` means the page came from cache and `read` means disk or OS cache. An all-hit plan says nothing about cold-cache latency.
- Watch for large `Rows Removed by Filter`, `Sort Method: external merge` (the sort spilled to disk), and nested loops with high `loops` counts.

Common hotspots to check: N+1 calls, unbounded result sets, sequential calls that could run in parallel, filters no index can serve (such as a leading-wildcard `LIKE`), per-request aggregation of data that rarely changes, oversized payloads, lock contention, connection-pool exhaustion, allocation/GC churn, and cache stampedes.

## Label every fix

Each recommended fix carries all of these fields:

- **Expected gain**: taken from a measurement, or labeled **estimate** with its basis (for example, "removes a node measured at 214 ms"). Never write a bare "X ms → Y ms".
- **Cost**: build time, storage, write amplification, memory, extra infrastructure, and code complexity. If the size or build time is unknown, say how to measure it on a copy.
- **Rollout risk**: locks, table rewrites, backfills, cache warm-up and invalidation, and deploy ordering, plus the mitigation and the rollback path. For database changes, name the facts and hand the full plan to `migration-safety`:
  - `CREATE INDEX CONCURRENTLY` runs outside a transaction.
  - Set `lock_timeout` for DDL on hot tables.
  - `ADD COLUMN` that is nullable or has a constant default is metadata-only.
  - Adding a **STORED generated column rewrites the table** under ACCESS EXCLUSIVE. Prefer an expression index when only a lookup is needed.
  - Backfills run in **batches**, never as one `UPDATE` of every row.
- **Behavior change**: "None" or exactly what users or callers will see differently. Optimizations that often change behavior include caching and denormalization (staleness, rounding), full-text search replacing `LIKE`/`ILIKE` (tokenization and stemming change which rows match), added limits or pagination, async/queued work (eventual consistency), parallelized calls (ordering, partial-failure semantics, load on downstream services), approximate counts, and weaker isolation. A behavior change needs product/owner sign-off. Report it as such, not as a pure speedup.

Prefer fixes that remove work (don't compute it, compute it once, index it) over fixes that do the same work faster. Prefer a no-behavior-change option when one exists, and list the behavior-changing alternative separately.

## Severity

Use the shared scale: 🔴 BLOCKER, 🟠 MAJOR, 🟡 MINOR, 💭 NIT. In performance terms:
- **🔴 BLOCKER**: can take the service down or lose data: unbounded memory, pool exhaustion under normal load, or a proposed fix whose rollout would lock or rewrite a hot table without mitigation.
- **🟠 MAJOR**: a measured bottleneck that breaks the target on a hot path, or an N+1.
- **🟡 MINOR**: a measurable but small cost, or a missing measurement that blocks a decision.
- **💭 NIT**: hygiene, such as `SELECT *` or unclear ordering, with no measured cost.

## Rules

1. **No invented numbers.** Every number comes from the input, a command you ran, or is labeled **estimate**.
2. **Biggest measured share first.** Don't optimize a phase that is 5% of the time while a 50% phase exists.
3. **Know when to stop.** Once the target percentile is met with headroom, list the remaining ideas under "Not Recommended" or leave them out.
4. **Verify semantics, not just speed.** Before calling a rewrite equivalent, diff its results against the old query or code on the same data.
5. **Guard against regressions.** Add an alert on the target percentile, plus a plan-shape or benchmark check where it is stable. Wall-clock assertions in shared CI are flaky, so avoid them.
6. **Stay in scope.** Recommend indexes and schema changes as fixes. Deep schema design belongs to `db-design`, and the migration runbook belongs to `migration-safety`.

## Output Format

```markdown
# Performance Review: [endpoint / query / job]

## Baseline
- **Operation & rate**: [what, calls/sec or /hour, critical path?]
- **Latency**: [p50 / p95 / p99 (max), source, window, or "not measured"]
- **Target**: [SLO, or "not stated: proposed X, confirm"]
- **Environment**: [prod / copy; data size; warm/cold cache; concurrency]

## Measurement Gaps
- [What is missing or unexplained → exact way to capture it]

## Where the Time Goes
| Phase | Measured time | Share | Source |
|---|---|---|---|

## Findings
### [🔴/🟠/🟡/💭] [Title]
- **Evidence**: [measurement, plan node, span, or file:line]
- **Hypothesis**: [mechanism]
- **Fix**: [specific change, minimal snippet]
- **Expected gain**: [measured, or "estimate: … (basis)"]
- **Cost**: [...]
- **Rollout risk**: [... + mitigation + rollback]
- **Behavior change**: [None / what changes; needs sign-off]
- **Verify**: [re-measurement and pass criterion]

## Not Recommended
- [Option]: [why not now, and what measurement would change that]

## Plan
1. [Ordered steps: close gaps → fix → re-measure → roll out → guard]
```

Order findings by severity, then by expected gain (measured share when gains are estimates). Omit sections that have no content, except Baseline and Plan. A worked example is in `examples/example.txt` (if installed). `template.md` mirrors this format.
