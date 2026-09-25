# SRE Engineering Templates

Use the template for the active mode (see SKILL.md). Headings and fields must match exactly.

---

<!-- Mode A — Incident Report -->

# Incident Report: [short description]

**Status**: [INVESTIGATING / MITIGATING / MONITORING / RESOLVED]
**Severity**: [SEV-1 / SEV-2 / SEV-3] — [one-line justification from the facts]
**Started**: [timestamp, or relative time as reported]
**Incident commander**: [name, or "unassigned — assign now"]
**Next update**: [time or interval]

## Impact
- **Users affected**: [number / % / segment, or unknown — ask]
- **Services affected**: [list]
- **Business impact**: [from input only, or unknown — ask]
- **Data integrity risk**: [none known / description]
- **Trend**: [growing / stable / shrinking / unknown — ask]

## Timeline
| Time | Event | Source |
|------|-------|--------|
| [time] | [event] | [user report / alert / observed] |

## Hypotheses
| # | Hypothesis | Status | Evidence for / against | Next check | Owner |
|---|------------|--------|------------------------|------------|-------|
| 1 | [cause] | [Open / Confirmed / Eliminated] | [facts] | [one concrete check] | [who] |

## Mitigations
| Option | Use if | Risk | Status |
|--------|--------|------|--------|
| [lever] | [hypothesis it addresses] | [what can go wrong] | [Proposed / Approved / Applied / Rejected] |

## Next Actions
- [ ] [action] — Owner: [who] — Due: [when]

## Status Update (draft)
> [known / not known / doing (by whom) / next update at]

## Open Questions
- [question whose answer would change severity, hypotheses, or mitigation]

## Follow-Up
- [ ] Post-mortem scheduled (required for SEV-1/SEV-2)
- [ ] Affected records identified and reconciled
- [ ] Detection gap reviewed (did an alert fire before users noticed?)

---

<!-- Mode B — SLO Spec -->

# SLO Spec: [service / user journey]

## SLIs
| SLI | Type | Good events / valid events | Measured at |
|-----|------|----------------------------|-------------|

## SLOs
| SLI | Target | Window | Error budget |
|-----|--------|--------|--------------|

## Alerts
| Alert | Burn rate | Long / short window | Budget spent at trigger | Routing | Runbook |
|-------|-----------|---------------------|-------------------------|---------|---------|

## Error Budget Policy
- [what happens when the budget is exhausted, who decides, exceptions]

## Findings on Existing Alerts
- [only when reviewing existing alerts; otherwise "n/a"]

## Assumptions & Open Questions
- [traffic volume, metric names, targets that need owner sign-off]

---

<!-- Mode C — Post-Mortem -->

# Post-Mortem: [title]

**Date**: [incident date] | **Severity**: [SEV-n] | **Duration**: [start → mitigated → resolved]
**Authors**: [names] | **Status**: [Draft / In review / Final]

## Summary
[2–4 sentences: what happened, who was affected, how it was fixed]

## Impact
- **Users / requests affected**:
- **Duration of user impact**:
- **Error budget consumed**: [% of window budget, or "no SLO defined"]
- **Data impact**:

## Timeline
| Time | Event | Source |
|------|-------|--------|

## Trigger, Root Causes, and Contributing Factors
- **Trigger**:
- **Root cause(s)**:
- **Contributing factors**:

## Detection and Response
- **Time to detect**: | **Time to mitigate**:
- **Went well**:
- **Went poorly**:
- **Where we got lucky**:

## Action Items
| Action | Type | Priority | Owner | Ticket |
|--------|------|----------|-------|--------|

## Open Questions
- [facts still unknown]
