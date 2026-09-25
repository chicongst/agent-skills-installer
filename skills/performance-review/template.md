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
