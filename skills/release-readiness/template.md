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
