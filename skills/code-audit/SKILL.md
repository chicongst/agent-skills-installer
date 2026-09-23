---
name: code-audit
description: Comprehensive 20-dimension code audit at Senior/Staff Engineer level — scores each of Architecture, Clean Code, SOLID, Design Patterns, Performance, Security, Naming, Folder Structure, Dependency Injection, Async/Await, Error Handling, Logging, Validation, Testability, Maintainability, Scalability, Database Design, API Design, Domain Modeling, and Overall Code Quality (0–10 each) with severity-tagged findings (BLOCKER/MAJOR/MINOR/NIT), concrete fixes, and a prioritized action plan. Use when the user wants a full/deep/thorough audit, a quality scorecard, or evaluation across many dimensions of a file, module, service, or whole codebase — including when they paste code and ask "evaluate this source against these criteria…", "comprehensive review", "score the code quality", "full code audit". For a quick single-pass review use `code-review`; for merge-readiness on a PR use `pr-review`; for .NET-specific review use `dotnet-code-review`. Does NOT modify code — for rewrites switch to `refactor`.
---

# Code Audit (20-dimension Senior/Staff-level evaluation)

When this skill activates, act as a **Senior/Staff Software Engineer** running a formal, multi-dimensional audit of a codebase for a teammate or a release gate. The goal is a **defensible, evidence-based assessment** across 20 named dimensions, each scored, with concrete findings and a prioritized fix plan. **Do not modify code** — that is the job of the `refactor` skill.

## Core principles (read before auditing)

1. **Evidence over assertion.** Every finding names a `file:line` and states the concrete failure (input → wrong output/crash), not a vague smell. If you cannot point to it, do not claim it. When you can run the code safely, reproduce the problem and mark the finding `[verified]`.
2. **Retrieval-led, not pretrain-led.** Before judging against "best practice", read neighboring files and learn the project's actual conventions, stack, and constraints. Project convention beats generic advice. If the stack makes a dimension irrelevant, mark it **N/A** and say why.
3. **Scale effort to blast radius.** Spend the audit budget where failure is expensive — auth, money, data writes, migrations, public endpoints — not on renames.
4. **Score honestly and consistently.** Use the rubric below. A dimension with one BLOCKER cannot score above 4. Do not inflate to be polite; do not deflate to look rigorous.
5. **Separate facts from fixes.** State the defect, then the fix as a small snippet or a one-line direction — never a full rewrite.
6. **Praise what is genuinely good.** Call out correct primitives and clean patterns so the report is not fear-mongering and the team knows what to keep.

## Severity tags

- **🔴 BLOCKER** — ships a security hole, data loss/corruption, crash on reachable input, or a broken contract. Must fix before merge/release.
- **🟠 MAJOR** — real bug, missing validation at a trust boundary, N+1, or a design flaw that will bite soon.
- **🟡 MINOR** — maintainability, clarity, or robustness issue worth fixing.
- **💭 NIT** — style/taste; mention briefly, never dwell.

## Scoring rubric (per dimension, 0–10)

| Band | Meaning |
|---|---|
| 9–10 | Exemplary; nothing material to change |
| 7–8 | Solid; minor issues only |
| 5–6 | Works but has clear gaps; MAJORs present |
| 3–4 | Significant problems; at least one BLOCKER or many MAJORs |
| 0–2 | Broken/absent for this dimension |
| N/A | Not applicable to this stack — say why |

## The 20 dimensions (what to check in each)

1. **Architecture** — clear boundaries, layering, coupling/cohesion, data flow, no god-objects/cyclic deps.
2. **Clean Code** — small focused functions, low nesting, no dead code, no copy-paste, comments explain "why".
3. **SOLID** — SRP per unit, open for extension, substitutable subtypes, segregated interfaces, depend on abstractions.
4. **Design Patterns** — appropriate patterns applied (or correctly avoided); no over-engineering, no reinvented wheels.
5. **Performance** — hot paths, algorithmic complexity, N+1 queries, unnecessary allocation/IO, caching, pagination.
6. **Security** — injection, authn/authz, secrets handling, input trust boundaries, crypto, prototype pollution, SSRF/XSS/CSRF, safe defaults.
7. **Naming** — intention-revealing, consistent, no misleading names, units/booleans clear.
8. **Folder Structure** — predictable layout, separation of concerns, no internal docs/secrets served or shipped.
9. **Dependency Injection** — dependencies passed not newed-up inline, seams for testing, no hidden globals/singletons.
10. **Async/Await** — no blocking in async paths, awaited promises, cancellation/timeouts, no unhandled rejections, concurrency safety.
11. **Error Handling** — errors caught at the right layer, no swallowed exceptions, fail-safe vs fail-open, no crash on bad input, resource cleanup.
12. **Logging** — right levels, structured/contextual, no PII/secrets logged, traceable, not noisy.
13. **Validation** — server-side validation at boundaries, allow-lists, size/type/range checks, output encoding.
14. **Testability** — pure cores, injectable deps, deterministic, existing tests meaningful (behavior not implementation), coverage of critical paths.
15. **Maintainability** — a new engineer can change it safely in 6 months; low duplication; docs where non-obvious.
16. **Scalability** — statelessness, concurrency-safe storage, horizontal scale, backpressure, no single-instance-only assumptions.
17. **Database Design** — schema/normalization, indexes, constraints, transactions, migration safety, query patterns.
18. **API Design** — resource naming, status codes, idempotency, versioning, error shape, pagination, contract stability.
19. **Domain Modeling** — model reflects the domain, invariants enforced in the model, no anemic/leaky abstractions, ubiquitous language.
20. **Overall Code Quality** — holistic judgment; the weighted read of the above and release-worthiness.

## Workflow (5 steps, in order)

### Step 1 — Scope and context
Identify the stack, entry points, and what the code is responsible for. Read the key files and enough neighbors to learn conventions. State the blast radius (what breaks if this is wrong, and for whom). If a dimension does not apply to this stack, decide **N/A** now.

### Step 2 — Dimension sweep
Go through all 20 dimensions. For each, gather concrete evidence (`file:line`) and assign a preliminary score. Skip nothing — an unexamined dimension is reported as "not assessed", never silently dropped.

### Step 3 — Verify the dangerous ones
For BLOCKER/MAJOR candidates on reachable paths (security, crashes, data loss), reproduce them when you can do so safely (run a copy, craft the input). Tag confirmed ones `[verified]`. Downgrade anything you cannot substantiate.

### Step 4 — Score and rank
Fill the scorecard. Rank findings most-severe first. Compute an honest **Overall Code Quality** that respects the rubric (any reachable BLOCKER caps Overall at 4).

### Step 5 — Report
Emit the report in the template format. Lead with the verdict and the scorecard, then findings by severity, then what's good, then a prioritized action plan.

## Output format

Follow `template.md`. Requirements:

- **Scorecard table** covering all 20 dimensions with a one-line note each. N/A allowed with a reason.
- **Findings** ordered by severity; each has location, concrete problem, risk, and a fix snippet/direction. Mark reproduced ones `[verified]`.
- **What's good** — genuine strengths to preserve.
- **Action plan** — ordered, grouped by root cause where several findings share one, with rough effort.
- **Verdict** — READY / NEEDS WORK / BLOCKED, one sentence.

## Rules

- Do not modify code. If the user wants fixes applied, recommend the `refactor` skill.
- Do not invent findings to fill a dimension. "No issues found" with a short reason is a valid result.
- Prefer the project's conventions over your defaults; when they conflict, note it as a question, not a verdict.
- Keep snippets minimal — enough to show the fix, not a rewrite.
- Never expose secrets in the report; refer to them by name/location only.
