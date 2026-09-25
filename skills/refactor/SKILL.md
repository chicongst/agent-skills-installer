---
name: refactor
description: Use when the user asks to refactor, clean up, simplify, restructure, or untangle existing code, or the code has deep nesting, duplication, god functions, premature abstractions, or scattered logic — and the goal is the same behavior with a clearer structure. Works in any language; modifies code in small verified steps behind a test safety net. Not for C#/.NET code (use `dotnet-code-refactor`), review-only feedback (use `code-review` or `code-audit`), fixing a bug (use `fix-bug` or `debug`), or finding or measuring performance problems (use `performance-review` or `algorithm-review`) — applying an already-verified, behavior-preserving rewrite from them is in scope.
---

# Refactor

Change the structure of existing code without changing what it does. The goal is code that is simpler and easier to change — not more files, layers, or abstractions.

**Refactoring = no observable behavior change.** Same return values, same errors (type and message), same side effects in the same order, same public API. Anything else — adding pagination or a transaction, changing an error message, trimming input, switching time zones, swapping a hash algorithm — is a behavior change. Never slip it into a refactor; report it separately (see Output format).

## Workflow (in order)

### 1. Understand and diagnose
- Read the code and its callers. Read 2–3 neighboring files to learn the project's conventions (naming, layout, error style, formatter). Project convention beats generic best practice.
- If you cannot state what the code does, ask the user before touching it (use AskUserQuestion if available, otherwise ask in plain text).
- List the smells with `file:line`, using the smell table below. If there are more than three, propose the top 2–3 and let the user choose; do not rewrite the whole file.

### 2. Classify risk for each move

| Risk | Typical moves | Handling |
|---|---|---|
| **SAFE** | Rename a local/private symbol; guard clauses over nested `if`s with identical outcomes; inline a single-use variable; remove code proven unreachable | Existing tests + compile/lint are enough |
| **RISKY** | Extract function/class; move code across modules; rename an exported symbol whose callers are all in this repo (list them first); introduce a parameter object; replace a conditional with polymorphism; touch async/concurrent code | Characterization tests must exist and pass **before** the change |
| **DANGEROUS** | Editing the logic of auth, credential handling, payments, DB schema or migrations, transactions/locks, message consumers, or security validation; changing a public API contract. (Moving such code verbatim within the same module, pinned by characterization tests, stays RISKY.) | Stop. Explain the risk, propose an approach, and get the user's confirmation first |

### 3. Check the safety net
1. Find the tests for the target (follow the project's naming, e.g. `test_*.py`, `*.test.ts`, `*_test.go`) and run them once as a baseline. If the baseline fails, stop and ask — do not refactor on top of red tests.
2. Judge quality: tests that only assert "was called" or mock the unit under test count as **no tests**.
3. If coverage is missing for a RISKY move, write **characterization tests** first: call the current code with concrete inputs (valid, each error branch, edge cases, wrong types), assert whatever it actually returns, raises, and does — bugs and quirks included. They pass on the old code by construction; they must still pass after.
4. Found a bug while characterizing? Pin it, do not fix it. List it under "Behavior changes recommended".
5. If the user refuses tests, only SAFE moves are allowed, and the report must say "no safety net — behavior not verified".

Present steps 1–3 as a plan (Status: Plan) and wait for confirmation when any move is DANGEROUS, when you had to pick among more than three smells, or when the user asked for a plan. Otherwise — the user asked you to refactor a specific target and every move is SAFE, or RISKY with characterization tests passing — apply directly.

### 4. Apply one move at a time
- One smell, one move, then run the tests. Green → next move. Red → undo that move (revert your edit, or `git stash` it) and investigate. Never "fix" a characterization test to make it pass, and never run `git reset --hard` or other destructive commands.
- Refactor first, feature/bug fix later — never in the same step or commit.
- Keep behavior-bearing details byte-for-byte: error messages, defaults (`get('name', '')` is not `get('name') or ''`), evaluation and side-effect order, exception types, log text.
- Do not change dependencies, import paths, or formatting of lines you are not refactoring. Run the project's formatter only if it already uses one.

### 5. Verify and report
Re-run the full suite and the linter; re-read the diff as a reviewer. Anything in the diff that is not in the plan gets reverted or moved to its own change. Then write the report.

## Smells and the matching move

| Smell | Signal | Move |
|---|---|---|
| Long function | Does several distinct things (validate, persist, notify…) | Extract Function per responsibility |
| Deep nesting | > 3 levels of `if`/loop | Guard clauses, early return |
| Duplication | Same logic with the same contract in 3+ places | Extract one shared function |
| Repeated expression | Same lookup or call written 3+ times in one scope | Introduce local variable |
| Mysterious name | `data2`, `tmp`, `handle`, `process` | Rename to intent |
| Magic literal | Unexplained number/string in logic | Named constant; enum for a closed set of variants |
| Flag argument | Boolean parameter switches behavior | Split into two explicit functions |
| Long parameter list | > 4 params that always travel together | Parameter object |
| Speculative generality | Interface, strategy, or factory with one implementation | Inline it |
| Middle man / pass-through wrapper | Function or class that only forwards calls | Remove it; call the target directly |
| Repeated type switch | Same `switch` on a type in several places | Polymorphism (only if it repeats) |
| Dead code | Unreferenced — verified by search, including reflection/DI/convention wiring | Delete (do not comment out) |
| Business logic in a handler | Route/controller computes domain rules | Move to wherever the project keeps domain logic |

## Judgment rules
1. **Every move needs a specific reason** ("removes 5 repeated lookups", "validation becomes testable alone"). "Cleaner" is not a reason.
2. **Extract Function when the block is a distinct responsibility with a nameable contract**, even if used once. Do not extract a single-use snippet under ~5 lines — inline beats indirection.
3. **Shared utilities and abstractions wait for the third real use.**
4. **Keep queries and config access next to their only caller.** Select explicit columns (`SELECT id, email FROM users WHERE id = ?`), not `SELECT *`.
5. **Wrap a dependency only when the wrapper adds value** — narrower interface, error translation, a test seam, or a swap that is actually needed.
6. **Follow the project's layout.** Put new code where similar code already lives; never introduce a folder convention the codebase does not use. If there is none, colocate with the feature. (Example: a NestJS project with per-module `enums/` gets new enums there; a Python project that colocates keeps colocating.)
7. **Create a new file only when the moved code has another caller or the project convention requires it.**
8. **Do not refactor** working code nobody needs to change, code you do not understand, or pure style.

## Output format

```markdown
# Refactor: [target]

**Status**: [Plan — awaiting confirmation / Applied]
**Safety net**: [✅ existing tests sufficient / ⚠️ characterization tests added first / ❌ none — user waived, behavior not verified]
**Conventions followed**: [what you learned from neighboring code]

## Smells
| # | Smell | Location | Move | Risk |
|---|---|---|---|---|
| 1 | [specific smell] | [file:line] | [move] | [SAFE / RISKY / DANGEROUS] |

## Steps
### Step N — [Move]: [one-line summary]
**Why**: [specific reason]
**Change**: [before → after snippet or diff]
**Verified by**: [test or command run, and its result; in a Plan, the test that will verify it]

## Behavior verification
- [commands run and results; concrete "input → same output/error before and after" evidence]

## Deliberately not changed
- [what looked tempting to extract or clean, and why it was left alone]

## Behavior changes recommended (not applied)
### [severity] [title]
**Location**: [file:line]
**Problem**: [what is wrong today]
**Proposed change**: [what to do, as its own change]
**Migration / rollout**: [data migration, compatibility, caller updates, or "none"]
```

Severity for recommendations: 🔴 BLOCKER (security hole, data loss/corruption, crash on reachable input, broken contract) / 🟠 MAJOR (real bug or design flaw that will bite soon) / 🟡 MINOR (maintainability or robustness issue worth fixing) / 💭 NIT (taste). Characterization tests added in step 3 of the workflow appear as Step 1. Omit a section that has no content instead of writing "none". A worked example is in `examples/example.txt` (if installed). `template.md` mirrors this format.
