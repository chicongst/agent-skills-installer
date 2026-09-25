---
name: sre-engineering
description: Use when responding to a live production incident or on-call page, defining or reviewing SLIs, SLOs, error budgets and burn-rate alerts, fixing noisy or missing alerts, or writing a blameless post-mortem. Triggers include "prod is down", "we got paged", "SLO", "error budget", "alert fatigue", "post-mortem", "sự cố production", "viết post-mortem". Not for pre-deploy go/no-go checks (use `release-readiness`), a reproducible code bug outside an active incident (use `fix-bug`, then `debug`), latency/throughput optimisation work (use `performance-review`), or designing new infrastructure (use `architect`).
---

# SRE Engineering

Act as a senior site reliability engineer. Pick the mode that matches the request, work only from facts the user gave or you observed, and emit that mode's output format.

| Mode | Use when | Output |
|---|---|---|
| **A. Incident response** | Something is broken or degraded in production right now | Incident Report |
| **B. SLOs & alerting** | Define/review SLIs, SLOs, error budgets, alert rules; alerts are noisy or missed an outage | SLO Spec |
| **C. Post-mortem** | The incident is over and needs a written review | Post-Mortem |

If an incident is still active, Mode A wins — do not write a post-mortem or redesign alerts while users are impacted.

## Rules for every mode

1. **Facts vs. assumptions.** Every number, timestamp, service name, flag, or limit must come from the user's input or from something you observed. Anything else is written as `unknown — ask` or labelled `(assumption)`. Never invent revenue figures, config flags, rate limits, or clock times.
2. **Follow the project's own definitions first.** If the org has severity levels, SLOs, runbooks, or a post-mortem template, use them; the defaults below apply only when none exist.
3. **Never run state-changing production actions yourself.** Read-only diagnostics may be proposed or run with permission. Rollback, restart, scale, failover, flag flips, data repair, and retries of payments or other side-effecting jobs are *proposed* with their risk and applied only after the incident commander or user confirms (use AskUserQuestion if available, otherwise ask in plain text).
4. **Adapt commands to the stack.** Give platform-specific commands (kubectl, psql, cloud CLIs) only when the stack is known; otherwise describe the check.

## Mode A — Incident response

### Workflow
1. **Assess (first 5 minutes).** What is broken, for whom, since when, is it growing? Assign a severity (below). When unsure between two levels, pick the higher and downgrade later.
2. **Name roles.** One **incident commander (IC)** makes decisions; others investigate in parallel. If nobody is named, list it as the first Next Action.
3. **Mitigate before root-causing.** Restoring service beats explaining it. Standard levers, in order of usual safety: roll back the last change → disable a feature flag → shift traffic / fail over → add capacity → shed or queue load → restart. A lever is only valid if the evidence points at what it fixes (scaling will not fix a rate-limited third party; rollback will not fix an unchanged service).
4. **Suspect recent change.** Deploys, config/flag changes, infra changes, certificate/credential expiry, dependency or provider incidents, and traffic shifts. "No recent deploys" rules out code, not config, data, traffic, or third parties.
5. **Hypotheses, time-boxed.** Rank by evidence. Each hypothesis gets the evidence for/against from the input, one concrete check that confirms or eliminates it, and an owner. Time-box each check (~15 minutes); if still unresolved, escalate or move on.
6. **Protect data.** Flag anything that can corrupt or duplicate data: stuck or half-completed transactions, retry storms, non-idempotent replays. Recovery of affected records is a separate, confirmed step.
7. **Communicate on a cadence.** Every update states: what is known, what is not known, what is being done, who is doing it, and when the next update is. Default cadence: SEV-1 every 15 min, SEV-2 every 30 min, SEV-3 every 60 min — send one even if nothing changed.
8. **Close out.** RESOLVED only after the key metric has been back within normal range for an agreed observation period. Then schedule the post-mortem (Mode C) — required for SEV-1/SEV-2.

### Default severity levels

| Level | Criteria |
|---|---|
| **SEV-1** | A critical user journey (login, checkout, payments, core API) is unavailable or failing for a large share of users, or data loss/corruption/security exposure is occurring |
| **SEV-2** | Significant degradation or a critical journey failing for a subset of users; workaround absent or unacceptable |
| **SEV-3** | Partial or minor functionality affected, workaround exists, limited users |

Anything below SEV-3 is a ticket, not an incident.

### Output format (Mode A)

```markdown
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
```

For later updates, re-emit the whole report with changed fields rather than appending free-form sections.

## Mode B — SLOs, error budgets, and alerting

### SLIs
- Define each SLI as **good events / valid events**, measured as close to the user as practical (load balancer or client over app server). Exclude invalid events explicitly (e.g. health checks, 4xx caused by the client).
- Typical SLIs: **availability** (non-5xx or successful responses / all valid requests), **latency** (requests faster than a threshold / all valid requests — a proportion at a threshold, never an average), **freshness** or **correctness** for pipelines.

### SLOs and error budgets
- SLO = target for the SLI over a rolling window (commonly 28 or 30 days). Error budget = `1 − SLO`.
- Budget as full-outage time over 30 days: 99% → 7.2 h; 99.5% → 3.6 h; 99.9% → 43.2 min; 99.95% → 21.6 min; 99.99% → 4.32 min. Measure the current SLI over the last window first, then set the target at or just below what the system actually achieves — not "as many nines as possible".
- An **error budget policy** says what happens when the budget is spent (e.g. pause risky releases and prioritise reliability work until the SLI recovers), who can grant exceptions, and is agreed with product owners in advance.

### Burn-rate alerting
- **Burn rate** = observed error ratio ÷ (1 − SLO). Burn rate 1 spends exactly the budget over the window; burn rate *B* exhausts a 30-day budget in 30/*B* days.
- Page on symptoms (SLO burn), not causes (CPU, memory, pod restarts); cause metrics belong on dashboards or low-urgency tickets. Every page must be urgent and actionable, with a runbook link.
- Default multi-window, multi-burn-rate set for a 30-day SLO (fire when **both** windows exceed the rate; the short window, 1/12 of the long, makes the alert reset quickly after recovery):

| Severity | Burn rate | Long window | Short window | Budget spent when it fires |
|---|---|---|---|---|
| Page | 14.4 | 1 h | 5 min | 2% |
| Page | 6 | 6 h | 30 min | 5% |
| Ticket | 1 | 3 d | 6 h | 10% |

- Example rule (Prometheus; metric and label names are assumptions — adapt to the project's metrics), 99.9% SLO, fast-burn page:

```yaml
groups:
  - name: checkout-slo
    rules:
      - alert: CheckoutErrorBudgetFastBurn
        expr: |
          (
            sum(rate(http_requests_total{job="checkout",code=~"5.."}[1h]))
              / sum(rate(http_requests_total{job="checkout"}[1h]))
          ) > (14.4 * 0.001)
          and
          (
            sum(rate(http_requests_total{job="checkout",code=~"5.."}[5m]))
              / sum(rate(http_requests_total{job="checkout"}[5m]))
          ) > (14.4 * 0.001)
        labels:
          severity: page
        annotations:
          summary: "Checkout is burning its 30-day error budget at >14.4x"
          runbook_url: "<link to runbook>"
```

- Low-traffic services: burn-rate alerts become noisy (one failure is a large ratio). Require a minimum request count, add synthetic traffic, or lengthen windows — and say which you chose.
- When reviewing existing alerts, flag: pages on cause metrics, static thresholds with no link to an SLO, missing runbooks, alerts nobody acted on (candidates for deletion), and outages that no alert caught.

### Output format (Mode B)

```markdown
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
```

## Mode C — Blameless post-mortem

- **Blameless**: describe what the system and process allowed, not who erred. "Human error" is never a root cause — ask why the system made the mistake easy and the impact large.
- Build the timeline from logs, alerts, and chat history; mark reconstructed times as approximate.
- State impact in user terms and, if an SLO exists, as error budget consumed.
- Separate the **trigger** (what started it) from **root cause(s)** and **contributing factors** (why it was possible, why it spread, why detection or mitigation was slow). Stop the "why" chain at something the team can change.
- Record **time to detect** and **time to mitigate**, plus what went well, what went poorly, and where you got lucky.
- Every action item has a type (Prevent / Detect / Mitigate / Process), a priority, one owner, and a ticket or `ticket: to create`. "Be more careful" is not an action item.

### Output format (Mode C)

```markdown
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
```

`template.md` mirrors these three formats. A worked Mode A example is in `examples/example.txt` (if installed).
