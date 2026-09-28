---
name: code-audit
description: "Use when the user wants a full, deep, or scored audit of a file, module, service, or whole codebase across many quality dimensions — a 0–10 scorecard over architecture, clean code, SOLID, patterns, performance, security, naming, structure, DI, async, error handling, logging, validation, testability, maintainability, scalability, database, API and domain modeling, with severity-tagged findings and a prioritized action plan. Any language, C# included. Triggers: \"full code audit\", \"score the code quality\", \"comprehensive review\", \"evaluate this source against these criteria\", \"đánh giá toàn diện code\". Not for a quick single-pass review (use `code-review`), PR merge readiness (`pr-review`), a security-only review (`security-review`), or applying fixes (`refactor`)."
---

# Code Audit

Run a formal, multi-dimensional audit the way a Staff engineer would for a release gate or a tech-debt decision: every score backed by `file:line` evidence, scored by fixed rules so two audits of the same code land on the same numbers, and a fix plan ordered by what matters. **Read-only** — to apply fixes, switch to `refactor` (or `dotnet-code-refactor` for C#).

## Principles

1. **Evidence or it isn't a finding.** Every finding names `file:line` and a concrete failure (input → wrong result, crash, leak). If you can run the code safely (a copy, a REPL, a test), reproduce BLOCKER/MAJOR candidates and tag them `[verified]`. If you can't point at it, don't claim it.
2. **Project convention beats generic best practice.** Read neighboring files first. Where the project's pattern conflicts with your preference, raise a Question, not a finding.
3. **Effort follows blast radius.** Spend the audit on auth, money, data writes, migrations, and public entry points, not on renames.
4. **Score by the rules below, not by feel.** Don't inflate to be polite or deflate to look rigorous.
5. **Don't guess missing context.** Unknown callers, deployment, or scale that would change a score go under Questions; say which score they would move.

## Step 1 — Scope

- **Which dimensions.** If the user names criteria ("evaluate against Architecture, Security, …"), score only those and list the rest in the scorecard as **Not requested**. Otherwise score all 20.
- **Which code.** For a file or module, read all of it. For a whole codebase, don't pretend to have read everything: map the entry points and layers, then read in depth the critical paths (auth, payments/money, data writes, public API) plus one representative module per layer. State the coverage in the report ("read in full: …; sampled: …; not read: …").
- **N/A** — a dimension that doesn't apply to this code (Database Design for a pure CLI) is N/A with a reason. It is not scored and doesn't count toward Overall.
- State the blast radius: what breaks if this code is wrong, and for whom.

## Step 2 — Sweep the dimensions

| # | Dimension | What to check |
|---|---|---|
| 1 | Architecture | Boundaries, layering, dependency direction, cyclic deps, god objects, data flow |
| 2 | Clean Code | Function size and focus, nesting, dead code, duplication, comments explain *why* |
| 3 | SOLID | One reason to change per unit, substitutable subtypes, narrow interfaces, depending on abstractions where a seam is needed |
| 4 | Design Patterns | Patterns that fit the problem; no speculative abstraction, no reinvented library features |
| 5 | Performance | Complexity on hot paths, N+1, unbounded reads, needless I/O or allocation, caching |
| 6 | Security | Injection, authn/authz and object-level access, secrets, trust boundaries, crypto, SSRF/XSS/CSRF, safe defaults |
| 7 | Naming | Intention-revealing, consistent, units and booleans clear, nothing misleading |
| 8 | Folder Structure | Predictable layout, feature vs layer consistency, nothing internal shipped or served |
| 9 | Dependency Injection | Dependencies passed in, no hidden globals/singletons, correct lifetimes |
| 10 | Async/Await | Awaited work, no blocking in async paths, timeouts/cancellation, unhandled rejections, concurrency safety |
| 11 | Error Handling | Right layer, nothing swallowed, fail-closed on security, resource cleanup |
| 12 | Logging | Levels, structure and context, no secrets/PII, useful for tracing |
| 13 | Validation | Server-side at every trust boundary, allowlists, size/type/range, output encoding |
| 14 | Testability | Pure cores, injectable deps, determinism; existing tests assert behavior and cover critical paths |
| 15 | Maintainability | A new engineer can change it safely; duplication, coupling, docs where non-obvious |
| 16 | Scalability | Statelessness, horizontal scale, backpressure, single-instance assumptions |
| 17 | Database Design | Schema, constraints, indexes vs queries, transactions, migration safety |
| 18 | API Design | Resource naming, status codes, error shape, idempotency, pagination, versioning |
| 19 | Domain Modeling | Invariants enforced in the model, ubiquitous language, no anemic or leaky model |
| 20 | Overall Code Quality | Computed — see Step 4 |

**One finding, one home.** Record each finding under the single dimension it primarily violates (SQL injection → Security, not also Validation and Clean Code). Other dimensions may mention it ("see B1") but it lowers only its home dimension. This stops one defect from being counted four times.

Walk every in-scope dimension. A clean dimension gets a one-line reason ("parameterized queries throughout, authz middleware on every route"), not silence.

## Step 3 — Verify and rank

Reproduce BLOCKER/MAJOR candidates on reachable paths when it is safe; tag `[verified]`. Downgrade or move to Questions anything you cannot substantiate. Merge findings with one root cause into one finding with every location listed. Order by severity, then blast radius.

**Severity** (shared scale):
- **🔴 BLOCKER** — security hole, data loss/corruption, crash on reachable input, or broken contract. Must fix before release.
- **🟠 MAJOR** — real bug, missing validation at a trust boundary, N+1 on a real path, or a design flaw that will bite soon.
- **🟡 MINOR** — maintainability, clarity, or robustness issue worth fixing.
- **💭 NIT** — taste; one line.

## Step 4 — Score

**Per dimension (0–10):** start from the band that matches the evidence, then apply the caps.

| Band | Meaning |
|---|---|
| 9–10 | Exemplary; nothing material to change |
| 7–8 | Solid; MINOR/NIT only |
| 5–6 | Works, with clear gaps |
| 3–4 | Significant problems |
| 0–2 | Broken or absent |

Caps: a dimension with a BLOCKER scores **≤ 4**; with a MAJOR (and no BLOCKER) **≤ 6**.

**Overall Code Quality** is not a judgment call: take the **median** of the scored dimensions (exclude N/A and Not requested), round down, then cap it at **4** if any reachable BLOCKER exists, or at **6** if any MAJOR exists. Show the arithmetic in its note ("median of 6 scores = 3; BLOCKER cap 4 → 3").

**Verdict**, applying the rules in order:
1. **BLOCKED** — any open BLOCKER.
2. **NEEDS WORK** — any MAJOR, or Overall below 7.
3. **READY** — otherwise.

## Step 5 — Report

`template.md` has the full skeleton; a worked example is in `examples/example.txt` (if installed). If the template isn't available, use these sections in this order:

1. `# Code Audit: [target]` with **Verdict**, **Blast radius**, and **Coverage** (read in full / sampled / not read).
2. **Scorecard** — one row per dimension: score, `N/A — reason`, or `Not requested`, plus a one-line note.
3. **Findings** by severity — each with ID, dimension, `file:line`, problem, risk (input → outcome), minimal fix.
4. **Questions** — what only the author can answer, and which score it could move.
5. **What's good** — specific strengths to keep.
6. **Action plan** — ordered, grouped by root cause, with rough effort.

## Rules

- Do not modify code.
- Don't invent findings to fill a dimension; a clean dimension with a reason is a valid result.
- Fixes are minimal snippets or one-line directions, never rewrites.
- Never paste secret values; refer to them by location.
- Don't write exploit payloads; describe the failure ("attacker-controlled `id` reaches the SQL string") and the fix.

If a skill named here isn't installed, say which one fits, then help as far as this skill's own scope and rules allow.
