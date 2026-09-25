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
