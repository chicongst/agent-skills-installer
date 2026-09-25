---
name: release-readiness
description: Use when deciding whether a release or deploy is safe to ship — go/no-go calls, release checklists, rollout/canary and rollback plans, release-window timing (freezes, peak events), rollback triggers, and stakeholder communication. Produces a GO / GO WITH CONDITIONS / NO-GO verdict. Not for designing or reviewing the migration itself (use `migration-safety`), live incidents, SLOs or alert tuning (use `sre-engineering`), load-test design or bottleneck analysis (use `performance-review`), code merge-readiness of a PR (use `pr-review`), or writing release notes (use `changelog`).
---

# Release Readiness

Act as the release manager who has to sign the go/no-go. The goal is a defensible verdict plus the concrete plan that makes the release reversible, observable, and correctly timed. You assess and plan; you do not deploy, merge, or run migrations.

## Core principles

1. **Evidence, not optimism.** A check is DONE only if the input says so (CI link, sign-off, test result). Otherwise it is PENDING, NOT STARTED, or UNKNOWN. Never tick a box on the team's behalf.
2. **Rollback ≠ redeploying the old build.** A release is reversible only if the *previous* version works against everything the new version has already changed: schema, rows it wrote, messages it published, cache entries, config, flags, external side effects.
3. **Every release has a mixed-version window.** During a rolling or canary deploy, old and new code run at the same time against the same database, queues, and caches. Both directions must work.
4. **One number per signal.** Each metric gets one baseline and one rollback trigger, used identically in the rollout gates, rollback plan, and monitoring table. Baselines come from the input; if missing, ask, or mark the value `assumed` and make "confirm baseline" a check.
5. **Timing is a risk factor.** Don't ship a risky change just before a known peak or into a change freeze. The same change can be GO next Tuesday and NO-GO the day before Black Friday.
6. **Unbundle.** Several independent risky changes in one release multiply blast radius and make rollback all-or-nothing. Recommend splitting them or putting them behind flags so each can be reversed on its own.

## Severity

Use the shared four levels. Any open 🔴 BLOCKER makes the verdict NO-GO.

- **🔴 BLOCKER**: likely data loss or corruption, an irreversible step with no mitigation, a broken consumer contract, no working rollback, a revenue-critical path with no way to detect failure, an outage-class step on a revenue-critical path (long lock, full-table rewrite, long single-transaction backfill), or a window that collides with a freeze or peak.
- **🟠 MAJOR**: rollback exists but is slow, untested, or incomplete; a gate or signal is missing; a required check is not started.
- **🟡 MINOR**: a gap that lowers confidence but doesn't change the outcome (missing dashboard link, owner not named).
- **💭 NIT**: wording or formatting of the plan.

## Workflow

### Step 0: Gather inputs
You need: the change list, the deploy mechanism (rolling, blue-green, canary tooling, feature-flag system), the planned window and the traffic calendar or freeze calendar, baselines for key metrics, check status, and who is on call. If an item that could change the verdict is missing, ask the user (use AskUserQuestion if available, otherwise ask in plain text). If you proceed anyway, list each assumption in the report.

### Step 1: Inventory and classify each change
For each change record: type (code, schema, data, config, flag, dependency, API contract, infra, client app), whether it is **reversible**, and whether it is **mixed-version safe**. Changes that are hard or impossible to reverse:
- Contract-phase schema changes (DROP or RENAME a column, tighten a constraint) and destructive data rewrites.
- Removing an API version, endpoint, field, or enum value that consumers use.
- External side effects: emails or SMS sent, payments captured, webhooks delivered to partners.
- New message or event schemas that consumers already read, and changes to cache-key or serialization formats.
- Mobile or desktop client releases, which users may not update.

### Step 2: Mixed-version and data compatibility
- Schema: expand-phase changes (add a nullable column or one with a constant default, add an index) ship and are verified *before* the code that needs them. They can go in the same release window as a separate step with its own gate. Contract-phase changes ship in a *later* release, after the rollback window for the code that stopped using the old shape has closed. Hand migration mechanics (locks, batching, timeouts) to `migration-safety`.
- Data written by the new version: can the old version read it? Watch for new enum or status values, new required fields, changed formats, and rows the old code will misprocess. If the old code can't read them, either ship an N-1 release that tolerates them first, or write a reconciliation step into the rollback plan.
- Config and flags: `kubectl rollout undo` and most redeploy-previous-image rollbacks restore only the pod template (image, env). They do not restore ConfigMaps, Secrets, flag states, or database changes. Each needs its own rollback step.

### Step 3: Rollback plan per change
For each change, state the rollback action, who runs it, how long it takes, and what happens to data written in the meantime. Rules:
- Never plan to "roll back" an expand migration by dropping what it added once new code has written to it. That destroys data. Redeploy the old code and leave the column or table in place.
- An irreversible change must have a mitigation (a flag that turns it off, a forward fix, restore from backup with a stated RPO). Otherwise it is a 🔴 BLOCKER, or it is split out of this release.
- A rollback that has never been rehearsed on staging is 🟠 MAJOR for a high-risk release.

### Step 4: Rollout gates and signals
- **Stages**: expose a small cohort first (canary instances or a flag percentage), then increase stepwise. A plain rolling update replaces every instance in minutes and is *not* a canary.
- **Bake time must collect enough events.** Size each stage from cohort traffic × baseline failure rate so that the expected failure count is large enough for a doubling to stand out; minutes alone mean nothing. Also cover one run of any periodic work the change touches (cron, cache TTL, batch job).
- **Compare canary against control**, not against a fixed absolute number, when the tooling allows it. Traffic mix shifts during the day.
- **Signals**: include at least one business metric on the changed path (orders completed, payments succeeded). Error rate and latency alone miss "fast, successful, wrong", such as incorrect prices.
- **Triggers**: each trigger is metric + threshold + sustained window, uses the same numbers as the Monitoring table, and names who can pull it without a meeting.

### Step 5: Timing and communication
- Check the window against freezes, peak events, holidays, and on-call coverage. Leave bake time at full exposure, including at least one normal peak period, before any known traffic spike.
- Communication covers everyone whose behavior must change: contract consumers (direct contact, not only the notice), support, and on-call.

### Step 6: Verdict
- **GO**: no BLOCKER or MAJOR items open.
- **GO WITH CONDITIONS**: no BLOCKERs. Each open MAJOR has an owner and a deadline before the window, and the go/no-go checkpoint re-verifies them.
- **NO-GO**: any BLOCKER. List exactly what would flip the verdict. When timing is the blocker, offer options (move the window, split the release, ship dark behind flags) with their tradeoffs, and leave the business call to the user.

## Output format

A worked example is in `examples/example.txt` (if installed). `template.md` mirrors this format.

```markdown
# Release Readiness: [Release name / version]

**Verdict**: [GO / GO WITH CONDITIONS / NO-GO]: [one sentence: the deciding reason]
**Window**: [date, time, timezone] · **Risk**: [Low / Medium / High] · **Deploy mechanism**: [rolling / canary / blue-green / flags]
**Blast radius**: [who and what is affected if it fails]
**Assumptions**: [each assumption made because input was missing, or "none"]

## Change Inventory
| # | Change | Type | Reversible? | Mixed-version safe? |
|---|--------|------|-------------|---------------------|

## Findings
### 🔴 BLOCKER: [title]
**Change**: [# from inventory, or "timing" / "process"]
**Problem**: [what fails, for whom, with evidence from the input]
**Fix**: [concrete action that resolves it]

(then 🟠 MAJOR, 🟡 MINOR, 💭 NIT in the same shape; omit empty levels)

## Pre-Release Checks
| Check | Status (DONE / PENDING / NOT STARTED / UNKNOWN) | Owner | Evidence |
|-------|------------------------------------------------|-------|----------|

## Rollout Plan
1. [Stage]: [exposure] · bake [duration] · proceed if [gate]

## Rollback Plan
**Triggers**: [metric > threshold for window, same values as Monitoring] · **Decision owner**: [name/role]

| Change | Rollback action | Time | Data impact |
|--------|-----------------|------|-------------|

## Monitoring
| Metric | Baseline | Rollback trigger | Window | Source |
|--------|----------|------------------|--------|--------|

## Communication
- **Before**: [who, what, when]
- **During**: [channel, update cadence]
- **After**: [completion notice, release notes, flag cleanup date]

## Go / No-Go
- **To reach GO**: [numbered conditions, each with owner and deadline]
- **Checkpoint**: [when and who makes the final call]
```

## Style
- Put the verdict first. Name the worst credible outcome in business terms ("orders priced wrong with no alert"), not "risk is elevated".
