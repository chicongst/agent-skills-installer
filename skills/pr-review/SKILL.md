---
name: pr-review
description: "Use when deciding if a change set (PR URL, branch vs base, or pasted diff) is ready to merge — \"review this PR\", \"is this ready to merge\". Judges the change as a unit: scope, size, hidden changes, blast radius, tests, rollout/rollback, description, plus blocking defects in changed lines; ends in APPROVE / REQUEST CHANGES / NEEDS DISCUSSION. Not for code quality of a file or module outside a change set (use `code-review`, or `dotnet-code-review` for C#), a scorecard audit (`code-audit`), a whole release (`release-readiness`), or a migration deep-dive (`migration-safety`)."
---

# PR Review

Act as the reviewer who has to click "merge": decide whether this change set is safe to merge, and what must change first. Do not modify code or git state.

**Boundary**: this skill judges the *change* (scope, description, tests, rollout, merge blockers in the diff); for a deep quality read of the code itself, use `code-review` (or `dotnet-code-review`).

## Step 0 — Get the change set

Never review from a description of a PR alone.

| Source | How to read it (read-only) |
|---|---|
| PR URL / number | `gh pr view <n>`, `gh pr diff <n>`, `gh pr checks <n>` if `gh` is available; otherwise ask the user to paste the diff and description |
| Local branch | `git log --oneline <base>..HEAD`, `git diff --stat <base>...HEAD`, `git diff <base>...HEAD` |
| Pasted diff / file list | Review what is present. If only a file list is given, you can judge scope, size and test presence, but say line-level findings need the diff |

Also read: the PR title and description, linked issue, CI status, and enough of the surrounding code to learn the project's conventions (neighbouring files, lint config, CONTRIBUTING, CLAUDE.md). Never check out, merge, rebase, or reset branches to review — if you need to run something, ask first. When a fact that affects the verdict is missing (target branch, CI result, who uses a changed module), ask the user (use AskUserQuestion if available, otherwise ask in plain text), or list it under **Questions for the Author**.

## Review passes (in order)

### 1. Intent and description
- Does the title match what the diff actually does?
- Does the description state **what** changed, **why**, **how it was tested**, **risk**, and **how to roll back**? Missing items are findings (usually 🟡 MINOR; 🟠 MAJOR when the missing item is a risky behavior the reviewer could not otherwise discover).
- Behavior changes not mentioned in the description (new defaults, changed status codes, changed error messages) are findings regardless of whether the code is correct.

### 2. Scope and size
- One concern per PR. If the title needs "and", or the diff mixes feature + refactor + formatting, name the separable parts and suggest the split.
- Count meaningful changed lines: exclude lockfiles, generated code, snapshots, vendored files. Around 400 meaningful lines is a common rule of thumb for the limit of careful review — not a hard rule. Say "reviewable" or "should split" and why.
- **Hidden changes** — list every one, even if correct: dependency or lockfile bumps, config/env changes, shared modules, CI/build files, migrations, feature-flag defaults, permissions, public API or schema changes.

### 3. Risk and blast radius
- Who consumes what changed? Grep callers of changed exports, shared config, and endpoints. A change to a shared client, base class, or config affects every consumer, not just the feature in the PR title.
- **Risk**: Low = isolated, easy to revert, covered by tests. Medium = touches a shared path or has untested branches. High = affects auth, money, data writes, migrations, every request, or a shared dependency — or can crash/corrupt on a reachable path.
- **Reversibility**: can the commit be reverted cleanly? Not if it runs a destructive or non-backward-compatible migration, emits events/data other systems persist, or changes a public contract clients already use.

### 4. Blocking defects in the changed lines
A focused correctness pass on the diff and the code it directly calls — not a full quality review:
- Error and failure paths: what happens when a dependency (DB, cache, HTTP call) fails? Unhandled async rejections, swallowed errors, fail-open vs fail-closed on security controls.
- Concurrency and atomicity: multi-step writes without a transaction, check-then-act races, non-atomic read-modify-write.
- Trust boundaries: input validated server-side, no secrets committed, no auth bypass, error responses don't leak internals.
- Contracts: status codes and response shapes (400 malformed/wrong type, 422 well-formed but semantically invalid; 401 vs 403; 409 conflict), pagination style consistent with the rest of the API, no silent breaking change for existing clients.
- Response handling: exactly one response or `next()` per request path.
- New wrappers around a third-party dependency: worth it only where they add value (narrower interface, error translation, test seam); pass-through wrappers are a finding.

If you can run the code safely (a copy in a temp dir, an existing test command), reproduce BLOCKER/MAJOR candidates and tag them `[verified]`. Otherwise say how you reached the conclusion.

### 5. Tests
- **Would the tests fail if the change were reverted or broken?** A test that passes with the feature removed does not cover it.
- New behavior, the main error path, and the boundary case (e.g. the request just over a limit) each have a test.
- Modified or deleted tests: did behavior intentionally change, or was the test bent to pass? Flag `.skip`/`.only`, weakened assertions, blindly regenerated snapshots, and mocks that replace the unit under test.

### 6. Rollout and operations
- Migrations must be backward compatible with the currently deployed code (expand → migrate → contract). For anything non-trivial, recommend `migration-safety`.
- New config/env vars: documented, have safe defaults, validated at startup.
- Deploy order across services; whether the change hits all users at once and needs a flag or staged rollout (only when the risk is real).
- Can operators see it working or failing (log/metric on the new failure path)?

### 7. Project conventions
Follow the conventions the project already has — layout, naming, error handling, test style, migration style. If there is no established convention, don't invent one; for new folders, group by feature/domain. Cite the file that shows a convention when flagging divergence from it. Framework rules apply only if the project has them (e.g. NestJS: request DTOs validated with class-validator).

## Severity

- **🔴 BLOCKER** — ships a security hole, data loss/corruption, crash on a reachable path, or a broken contract. Must fix before merge.
- **🟠 MAJOR** — real bug, missing validation at a trust boundary, core behavior untested, undisclosed change to shared behavior, or a design flaw that will bite soon.
- **🟡 MINOR** — maintainability, clarity, robustness, or description gap worth fixing.
- **💭 NIT** — style/taste; one line, never dwell.

## Verdict rules

- **REQUEST CHANGES** — any BLOCKER, or any MAJOR the author has not explicitly agreed to defer to a tracked follow-up.
- **NEEDS DISCUSSION** — no blocking defect, but a decision only the team can make (product policy, design direction, rollout risk) must be answered before merge.
- **APPROVE** — only MINOR/NIT remain; say "approve with nits" if you listed any.

## Rules

1. **Evidence**: every finding cites `file:line` (new-side line numbers of the diff) or `(PR-wide)`, states the concrete failure (input/condition → wrong result), and gives a fix. Keep fix snippets minimal and make sure they are correct — a fix that introduces a new bug is worse than none.
2. **No invented facts**: use only what is in the diff, the description, the repo, and CI output. If you need a number or fact you don't have (traffic, client usage, Redis version), ask — don't assume.
3. **Unknown ≠ defect**: things you cannot determine go under Questions, not Findings.
4. **Review the tests as code** — bad tests are a finding, not a pass.
5. **Don't approve what you don't understand** — ask instead.
6. **One pass**: deliver all findings at once. Omit empty severity sections.
7. **Specific, neutral tone**; praise only what is specific and true.

## Output format

```markdown
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
```

`template.md` mirrors this format. A worked example is in `examples/example.txt` (if installed).
