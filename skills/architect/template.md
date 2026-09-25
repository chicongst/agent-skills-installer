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
| | | | | |

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
| | | | | |

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
