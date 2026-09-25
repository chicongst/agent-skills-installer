---
name: code-review
description: Use when reviewing code in any language except C#/.NET — a snippet, function, file, module, or diff — for bugs, correctness, edge cases, security and performance red flags, maintainability, and tests, including when the user pastes code and asks "any issues?", "is this OK?", "review this code". Single pass: severity-tagged findings with fixes and a verdict; does not edit code. Not for C#/.NET (use `dotnet-code-review`), merge readiness of a PR or change set (`pr-review`), a scored multi-dimension audit (`code-audit`), a deep security review (`security-review`), or applying fixes (`refactor`).
---

# Code Review

Review code the way a senior engineer reviews a teammate's work: find the real problems, prove them, rank them, and say how to fix each one.

## Principles

1. **Evidence, not vibes.** Every finding names `file:line` and a concrete failure: this input → this wrong result, crash, or leak. If you can run the code safely (a copy, a REPL, an in-memory DB), reproduce it and tag the finding `[verified]`. If you cannot point at it, do not claim it.
2. **Effort follows blast radius, not line count.** A 10-line auth change deserves more scrutiny than a 300-line new report page.
3. **Project convention beats generic best practice.** Read neighboring code before calling a pattern wrong. If conventions conflict with your preference, raise a question, not a finding.
4. **Substance over style.** Don't repeat what the compiler or linter reports; formatter-level issues are at most a NIT. Spend the review on logic, data, security, and tests.
5. **Don't guess missing context.** Never invent conventions, numbers, or context absent from the code or the user's message. If the code calls symbols you cannot see, or its intent is unclear, ask — as a Question in the report, or up front if you cannot review without it.

## Severity

| Tag | Meaning | Typical examples |
|---|---|---|
| 🔴 **BLOCKER** | Ships a security hole, data loss/corruption, crash on reachable input, or a broken contract. Must fix. | Injection, missing authz check, secret in code, lost write, API change that breaks callers |
| 🟠 **MAJOR** | Real bug, missing validation at a trust boundary, N+1, or a design flaw that will bite soon. | Off-by-one on a limit, money in floats, swallowed exception, check-then-act race, disabled test hiding a bug |
| 🟡 **MINOR** | Maintainability, clarity, or robustness issue worth fixing. | Ambiguous return value, stale comment, missing edge-case test, convention drift |
| 💭 **NIT** | Taste. One line, no fix snippet needed. | Naming polish, missing type hint |

Put design-level uncertainty ("should this even work this way?") under **Questions**, not as a severity.

## Workflow

### 1. Context and blast radius
- State in 1–2 sentences what the code does. If you can't, ask the user (use AskUserQuestion if available, otherwise ask in plain text) before reviewing.
- Given a diff, read the changed lines plus enough surrounding code to know the callers and the data flow.
- Classify the blast radius and state it in the report:

| Blast radius | Signals |
|---|---|
| **CRITICAL** | Auth/authz, money, data writes/migrations, shared libraries/middleware, CI/CD, infra |
| **HIGH** | Public API surface, message consumers/producers, cross-module contracts, persistence config |
| **MEDIUM** | New feature inside an existing module following an existing pattern, internal services |
| **LOW** | Docs, logging, private renames, test-only changes |

For LOW, a quick read and a short report is enough. Ask whether code is production-bound or a spike if it matters; spikes get a correctness pass only.

### 2. Slop scan (cheap, do it first)
Patterns that make broken code look finished — usually MAJOR, BLOCKER if they hide a BLOCKER:
- **Disabled or hollow tests:** `.skip`, `xit`, `@pytest.mark.skip`, `@Disabled`, `t.Skip()`, commented-out tests, assertions that can't fail (`expect(true).toBe(true)`, `assert result is not None` where the value matters).
- **Silenced tooling without a reason:** `@ts-ignore`, `eslint-disable`, `# type: ignore`, `# noqa`, `//nolint`, `@SuppressWarnings`.
- **Swallowed errors:** empty `catch`/`except`, catch-all that logs and returns `null`/`false`/default.
- **Shortcuts:** hardcoded secrets, new `TODO/FIXME/HACK`, dead branches (`if (false)`), un-awaited promises/futures, ignored error returns (Go `_ = err`).

### 3. Dimension pass
Walk every dimension. If one is clean, record it under **Checked OK** with a short reason so the reader knows it was examined.

- **Correctness & edge cases** — Trace each input through the code with: empty/null/missing, zero, negative, boundary (`<` vs `<=` on limits and indexes), duplicates/repeat calls, very large, Unicode, "not found" lookups. Also: error paths and partial failure (half-written state, missing transaction), check-then-act races on shared state, resource cleanup (files, connections, locks), money or IDs in floating point, time zones and clocks, integer overflow/division by zero.
- **Security (quick check)** — Untrusted input reaching SQL/shell/HTML/file paths/deserializers/URLs fetched server-side; missing authn/authz on new entry points; secrets or PII in code or logs; weak crypto or non-crypto randomness for tokens. For anything beyond a quick check, recommend `security-review`.
- **Performance** — Queries or I/O inside loops (N+1), unbounded reads/pagination, blocking calls in async paths, wrong data structure for membership checks, repeated work on a hot path. Any claim of "slow" must cite a measurement from the input or be labeled an estimate.
- **Maintainability** — Names that hide intent, ambiguous return values (`None` meaning three different things), deep nesting, duplication, comments that contradict the code, abstractions built for one caller.
- **Tests** — Does a test cover each new branch and the edge cases you found? Would the existing tests fail if the bug you found were present? Over-mocking that tests only the mocks.

### 4. Convention check
Read 2–3 similar files in the same module and compare naming, error handling, return types, and structure. Drift is usually MINOR; breaking a core pattern (e.g., bypassing the project's data-access layer) is MAJOR. If no neighboring code is available, write "No project context — reviewed against general practice only."

### 5. Verify and rank
- Reproduce BLOCKER/MAJOR candidates when safe; tag `[verified]`. Downgrade or move to Questions anything you cannot substantiate.
- Merge findings with one root cause into one finding; list each location.
- Order by severity; within a severity, by blast radius.

## Verdict rules

Pick exactly one, applying the rules in order:
1. **REQUEST CHANGES** — any BLOCKER or MAJOR.
2. **NEEDS DISCUSSION** — no BLOCKER/MAJOR, but an open Question could change the approach itself (intent unclear, design likely wrong). Line-level fixes wait until it is answered.
3. **APPROVE WITH COMMENTS** — at least one MINOR, no BLOCKER/MAJOR (NITs and Questions may accompany).
4. **APPROVE** — no findings, or NITs only.

When a BLOCKER or MAJOR exists, open Questions still go in the report, but the verdict stays REQUEST CHANGES.

## Output format

A worked example is in `examples/example.txt` (if installed). `template.md` mirrors this format.

````markdown
# Code Review — [file / function / change]

**Blast radius:** [CRITICAL / HIGH / MEDIUM / LOW] — [one-line reason]
**Findings:** 🔴 [n] · 🟠 [n] · 🟡 [n] · 💭 [n]
**Verdict:** [REQUEST CHANGES / NEEDS DISCUSSION / APPROVE WITH COMMENTS / APPROVE]

## Summary
[2–4 sentences: what the code does, the most important problem, why this verdict.]

## Findings

### 🔴 BLOCKER
#### [B1] [Short title] [verified]
**Location:** `path/file.ext:L10-L12`
**Problem:** [Concrete failure: input → outcome]
**Risk:** [What happens in production]
**Fix:**
```[lang]
[minimal snippet]
```

### 🟠 MAJOR
[Same fields as BLOCKER, IDs M1, M2…]

### 🟡 MINOR
[Same fields; Fix may be one line. IDs m1, m2…]

### 💭 NIT
- `path/file.ext:L5` — [one line]

## Questions
- [Question for the author, and which finding or verdict it could change]

## Checked OK
- [Dimension]: [why it's fine]

## What's good
- [Specific strength worth keeping]
````

Omit a severity section that has no findings; write "None" under Questions / Checked OK / What's good if empty. Never paste secret values into the report — refer to them by location.

## Special situations
- **Snippet with no callers visible:** review it standalone and say which risks depend on the callers (e.g., "BLOCKER if `order_id` comes from the client").
- **Huge diff (>500 lines):** say so, split by module, review the highest blast-radius part first.
- **User asks for one dimension only** (e.g., "just performance"): do that dimension plus the slop scan; list other dimensions as not assessed.
- **User wants the fixes applied:** finish the review, then switch to `refactor`, one finding at a time with tests.

## Don't
- Don't edit the code, and don't rewrite the whole function in a Fix — minimal snippets only.
- Don't pad with praise or filler; "What's good" is for specific things to preserve.
