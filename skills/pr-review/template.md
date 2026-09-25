# PR Review: [PR title]

**Source**: [PR URL / branch vs base / pasted diff] · **CI**: [passing / failing: which job / unknown]

## Summary
[2-3 sentences: what the PR does, the verdict, the single biggest issue]

## Change Analysis
- **Scope**: [Focused / Mixed — name the separable concerns]
- **Size**: [N files, +A −D; meaningful lines — reviewable / should split]
- **Hidden changes**: [none / list: config, dependency, shared module, migration, ...]
- **Risk**: [Low / Medium / High — what it touches and who is affected]
- **Reversibility**: [Revert-safe / Needs coordinated rollback / Irreversible — why]
- **Description**: [Complete / Missing: what, why, testing, risk, rollback]

## Findings

### 🔴 BLOCKER
#### [n]. [Title] — `file:line` [verified]
**Problem**: [condition → wrong result, and why it matters]
**Fix**: [minimal snippet or one-line direction]

### 🟠 MAJOR
#### [n]. [Title] — `file:line`
**Problem**: [...]
**Fix**: [...]

### 🟡 MINOR
#### [n]. [Title] — `file:line`
**Problem**: [...]
**Fix**: [...]

### 💭 NIT
- `file:line` — [observation]

## Missing from the PR
- [ ] [tests / docs / config documentation / migration that should be in this PR]

## Questions for the Author
1. [question whose answer could change the verdict]

## What's Good
- [specific, true observation]

## Verdict
**[APPROVE / REQUEST CHANGES / NEEDS DISCUSSION]** — [one sentence tied to the verdict rules]

## Merge Checklist
- [ ] CI passing
- [ ] All BLOCKER and MAJOR findings fixed or explicitly deferred to a tracked follow-up
- [ ] Tests fail without the change and pass with it
- [ ] Description covers what, why, testing, risk, rollback
- [ ] Rollout and rollback confirmed (migrations, config, flags), if applicable
