---
name: architect
description: "Use when designing a new system or service, choosing between architectural options (monolith vs. service, sync vs. async, which broker/store), reviewing the architecture of a design doc, or planning how a system handles growth, failure, consistency and migration. Produces a numbers-driven design: options, decision, failure modes, rollout, cost. Not for endpoint/contract design (use `api-design`), schemas and indexes (`db-design`), step-by-step data migrations (`migration-safety`), go/no-go on a release (`release-readiness`), or live incidents and alert tuning (`sre-engineering`)."
---

# Architect

Turn a problem statement into a design another engineer can build, operate and argue with: every choice tied to a number or a stated constraint, every rejected option named, every failure path handled.

## Step 0 — Gather context before designing

- **Existing system**: if a repo is available, read it — deployment config, DB, queues, how the current feature works. The cheapest architecture usually extends what already runs.
- **Numbers you need**: current load (average and peak, per second), known growth (with a date), data volume, latency/freshness SLOs, what may be lost or duplicated, team size and on-call, hosting constraints, budget.
- If a number that would change the decision is missing, ask the user (use AskUserQuestion if available, otherwise ask in plain text). If they want a draft anyway, proceed with each gap written as a labeled **Assumption**, and list it in Open Questions.
- Never invent a measurement. Anything not from the input is either derived (show the arithmetic) or labeled *estimate* with what would confirm it (load test, vendor quote).

## Workflow

### 1. Requirements & constraints
- Convert every load figure to per-second, separate steady state from peak, and state peak duration. `500k/min` is `8,333/s`; how long it lasts decides whether a queue can absorb it.
- Size to the **SLO**, not the arrival peak: if 3M messages must finish within 30 min, the drain rate is `3M / 1,800 s = 1,667/s`, regardless of how fast they arrive.
- Write non-goals. Classify data by loss tolerance: must-not-lose, may-duplicate, may-drop-if-counted.

### 2. Options (at least two, one of them the simplest that could work)
- Always include "extend the existing system" as an option and evaluate it against the numbers. Reject it only with a number or a hard constraint.
- For each option: fits current load? fits known growth? new infrastructure the team must operate? migration size? Put the comparison in a table.

### 3. Decision, reversibility, breakpoints
- Choose. State the one or two reasons that decided it.
- Classify reversibility: **two-way door** (swap cost is small — e.g. broker behind a thin publish/consume adapter) or **one-way door** (data model spread across services, deleting the old path, public contracts). Spend analysis on one-way doors.
- **Start simple, but not naive**: design for current load plus *known* growth. For each scaling limit of the chosen design, name the **breakpoint** — the measurable signal (e.g. "primary DB CPU > 70% during peaks") — and the next step when it trips. Do not build that next step now.

### 4. Data consistency
For every write that crosses a boundary (DB → broker, service → service, service → provider):
- **Source of truth**: which store is authoritative.
- **No dual writes**: "write DB, then publish" loses or invents events on a crash between the two. Use a transactional outbox (row written in the same transaction, relayed afterward) or CDC.
- **Delivery semantics**: at-least-once is the default; say where duplicates can arise and the idempotency key that absorbs them. "Exactly-once" end-to-end with an external provider is not available — say what duplicates are accepted.
- **Ordering**: needed or not; if needed, the key it is scoped to.
- **What can be lost**: must be explicit. Never buffer must-not-lose data only in process memory; a restart erases it. If loss is accepted, state the bound, why it is acceptable, and how it is counted.

### 5. Failure modes
For each dependency, walk: down, slow, erroring, returning duplicates, backlog far larger than normal. For each, give impact, how you detect it, mitigation, recovery.
- Timeouts on every remote call; retries with backoff and a cap; a dead-letter destination with an owner.
- Backpressure: where does work wait when a consumer is slower than a producer? It must be a durable store with a retention you've checked.
- Bulkheads: separate queues/pools so bulk traffic cannot starve latency-sensitive traffic.
- A circuit breaker that stops consuming beats burning retry budgets during a long provider outage.

### 6. Observability
Tie every alert to an SLO or a loss condition: queue age vs. latency SLO, dead-letter depth for must-not-lose data, outbox lag. Name the metric, threshold and who is paged. Propagate a correlation id from the originating request to the final side effect.

### 7. Rollout & migration
- Phase so each step is independently shippable and reversible; give the validation gate and rollback for each.
- Moving a side effect (sending email, charging a card) must never run both paths for the same item — decide per item at write time (flag per type/tenant), not by shadow traffic.
- Name the irreversible step (deleting the old path, dropping a table) and its entry criteria.
- Schema changes: route details to `db-design` / `migration-safety`; ship-day checks to `release-readiness`.

### 8. Cost
Derive from the numbers: request/message counts per month, storage growth, compute sized to the drain rate. If you do not know a price, give the billable quantity and say "multiply by current list price". Include operational cost: new systems someone must be on call for.

## Rules

1. **Every number has a source** — the input, arithmetic shown from the input, or an *estimate* label.
2. **Service boundaries follow data ownership.** Two deployables that must release together, or share tables they both write, are one service with network overhead. A separate *deployment* (own scaling, own failure domain) is often what's actually needed — not a separate codebase and database.
3. **Name what you are giving up** for each decision; a tradeoff with no cost listed is not analysed.
4. **Challenge requirements that drive cost** — "must this be real-time, or is 60 s fine?" — and show how the answer changes the design.

## Output Format

`template.md` mirrors this format. A worked example is in `examples/example.txt` (if installed).

```markdown
# Architecture Design: [System Name]

## Requirements & Constraints
- **Goal**: [what and why]
- **Non-goals**: [explicitly out of scope]
- **Load**: [steady / peak per second, peak duration, source of each number]
- **Known growth**: [what, by when]
- **SLOs**: [latency / freshness / completion targets]
- **Data loss tolerance**: [must-not-lose / may-duplicate / may-drop-if-counted, per data class]
- **Constraints**: [stack, hosting, team, budget]
- **Assumptions**: [anything not in the input, labeled]

## Options Considered
| Option | Current load | Known growth | New ops burden | Verdict |
|--------|--------------|--------------|----------------|---------|

## Decision
- **Chosen**: [option] — [deciding reasons]
- **Giving up**: [costs accepted]
- **Reversibility**: [two-way / one-way door per major choice, and what makes reversal expensive]

## Components
### [Component]
- **Responsibility**:
- **Data owned**:
- **Interface**: [endpoints, queues, events]
- **Scaling**: [unit of scale and what drives it]

## Data Flow
[diagram + numbered steps for the primary path]

## Data Consistency
- **Source of truth**:
- **Boundary writes**: [outbox / CDC / single write]
- **Delivery semantics & idempotency**: [where duplicates arise, dedupe key]
- **Ordering**:
- **What can be lost**: [none / bounded + justification + how counted]

## Failure Modes
| Failure | Impact | Detection | Mitigation | Recovery |
|---------|--------|-----------|------------|----------|

## Capacity & Growth
- **Derivations**: [arithmetic from the input]
- **Breakpoints**: [signal → next step, for each scaling limit]

## Observability
- **Metrics**:
- **Alerts**: [condition → threshold → who is paged, tied to an SLO or loss]
- **Dashboards**:
- **Tracing**: [correlation id path]

## Rollout & Migration
1. [Phase] — validation gate: [...] — rollback: [...]
- **Irreversible step**: [what, and entry criteria]

## Cost
- **Infrastructure**: [billable quantities derived from load]
- **Operational**: [what the team must now run and be on call for]

## Open Questions
- [question — what answer would change]
```
