---
name: test-writer
description: Use when designing or writing tests for a function, module, API, or bug fix — test plans, unit/integration test cases, edge cases, regression tests for a fixed bug, or characterization tests before a refactor. Derives expected values from the spec, runs the tests, and reports bugs or dead code found along the way. Triggers include "write tests", "add test cases", "test plan", "viết test", "viết unit test". Not for finding the root cause of an already-failing test (use `debug`), reviewing code quality (use `code-review`), or restructuring code (use `refactor`).
---

# Test Writer

Design and write tests that catch real bugs, with expected values you can defend line by line.

## Step 0 — Establish Context

- **Unit under test**: read the code and its direct callers. If the user named something you cannot find, or the scope is unclear ("test the service"), ask which unit and which behaviors matter. Use AskUserQuestion if available, otherwise ask in plain text.
- **Spec**: find what the code is *supposed* to do — docstring, comments, ticket, README, the user's words. The code is not the spec. If no spec exists, your tests are **characterization tests** of current behavior; say so in the plan.
- **Project conventions**: find existing tests, the framework, fixtures/factories, file naming and location, and the run command (`package.json` scripts, `pytest.ini`/`pyproject.toml`, `Makefile`, `go test ./...`, CI config). Follow them. If the project has no tests, use the language's standard framework and state that choice as an assumption.

## Workflow

1. **Map behaviors.** List every branch, guard, raise/throw, clamp, and side effect with its line number (if the input has no line numbers, count from the first line of the pasted snippet and say so in Scope). Partition each input into equivalence classes (valid, boundary, invalid, special values).
2. **Check reachability.** For each branch, guard, and clamp, find a concrete input that triggers it. If no input can, the code is dead or the spec and code disagree — record a finding. Do not write a test that pretends it fires. Line coverage will not catch this: `min(x, cap)`, ternaries, and `a or b` count as covered even when the interesting side never runs.
3. **Derive expected values by hand.** Compute each expected value from the spec, and show the arithmetic in the Derivation column (`100 × (1 − 0.20) = 80.00`). Never run the code and paste its output as the expectation — that only proves the code equals itself. The one exception is a characterization test, labeled as such. If a hand-computed value disagrees with the code, recompute once. If it still disagrees, it is a finding.
4. **Handle spec–code conflicts explicitly.** When a derived expectation exposes a bug, do not assert the buggy value and do not change production code unless asked. Report it under Findings, then either write the test for the intended behavior marked expected-to-fail with the finding ID (`@pytest.mark.xfail(strict=True, reason="F2: …")`, `test.failing` in Jest, or `t.Skip("F2: …")` in Go, which has no expected-failure marker — then also list it under Coverage Gaps so it is revisited), or leave it out and list it under Coverage Gaps. When intent is ambiguous, pin current behavior in a clearly labeled test and raise the question. Never weaken an assertion, or silently skip or delete a failing test, to get green.
5. **Pick the level.** Unit tests for pure logic. Integration tests when correctness depends on real DB, queue, or HTTP semantics (transactions, constraints, serialization) — do not mock the thing you are verifying. E2E only for a few critical user journeys. Label honestly: a test that touches a real database is an integration test.
   - **Isolation**: wrap each test in a transaction that is rolled back, truncate the touched tables, or use an isolated schema or throwaway container (e.g. Testcontainers) — never a shared dev database.
   - **Endpoints**: assert status code, response body shape, relevant headers, and the side effect (row written, message published), not just the status.
6. **Write the tests** following the Rules below.
7. **Run them.** Use the project's command, or the framework default (`pytest -q path`, `npx jest path`, `go test ./pkg/...`). If a test fails, decide whether the expectation or the code is wrong by re-deriving it, not by copying the actual value. If you cannot run the tests (no environment, missing dependencies), write "Not run" with the reason and the exact command. Never claim tests pass without output to show it.

## Case Checklist

- **Boundaries**: exactly at, just below, just above each threshold. Also zero, negative, the smallest valid unit (one cent, one item), maximum sizes, and empty / single / many collections.
- **Special values**: `null`/`None`/`undefined`, empty vs whitespace strings, Unicode, and case variants of string keys. For floats, `NaN` and `±inf`: every comparison with `NaN` is false, so a guard like `x <= 0` lets `NaN` through.
- **Combinations**: when options stack (tiers × coupons, flags × roles), parametrize the full cross product if it is small (up to about 20 cases); otherwise use pairwise selection plus the extremes.
- **Money and rounding**: binary floats misround decimal halves (`round(2.675, 2)` is `2.67` in Python), so prefer decimal types for money. Assert exact values only when the unit rounds its output. Otherwise use `pytest.approx` / `toBeCloseTo`.
- **Time and randomness**: inject or freeze the clock (`freezegun`, `jest.useFakeTimers()`, a clock parameter) and seed the RNG, in unit and integration tests alike. Cover time zones, DST transitions, and month or year ends when dates are involved.
- **Errors**: every raise/throw gets a test that asserts the type and a message fragment. For external calls, cover timeout, error status, malformed response, and retry idempotency.
- **State**: double submit, duplicate webhook or message delivery, out-of-order events, and partial failure mid-operation.
- **Regression**: for a bug fix, the new test must fail on the old code. Say how you confirmed that (ran it before the fix, or reasoned from the diff).

## Rules

1. **One behavior per test, Arrange-Act-Assert.** Put tables of similar cases in a parametrized test instead of copying the test body.
2. **Names state behavior and condition**: `test_returns_404_when_user_not_found`, not `test_get_user_3`.
3. **Independent and deterministic.** No shared mutable state and no order dependence. Unit tests make no real network, clock, or filesystem calls.
4. **Mock only at boundaries you don't own** (HTTP clients, queues, clock). Never mock the unit under test. Assert on outputs and observable effects, not on which internal functions were called:

   ```python
   # Good: survives refactoring
   assert checkout(premium_user, cart_of_100).total == 90

   # Bad: breaks if the discount logic is inlined, and passes even if the total is wrong
   discount_service.calculate.assert_called_once()
   ```

## Output Format

```markdown
# Test Plan: [unit under test]

## Scope & Assumptions
- **Unit**: [function/module/endpoint, file path]
- **Level**: [Unit / Integration / E2E]
- **Framework & location**: [framework, test file path, following project convention or stated default]
- **Spec source**: [docstring / ticket / user statement / none — characterization]
- **Assumptions**: [anything taken as given]
- **Out of scope**: [what is not tested and why]

## Findings
| ID | Severity | Location | Finding | Evidence | Suggested action |
|----|----------|----------|---------|----------|------------------|
| F1 | [🔴 BLOCKER / 🟠 MAJOR / 🟡 MINOR / 💭 NIT] | [file:line] | [bug, dead code, or spec question] | [input → actual vs expected] | [fix or question for owner] |

## Test Cases
| # | Category | Test name | Input | Expected | Derivation | Protects against |
|---|----------|-----------|-------|----------|------------|------------------|
| 1 | [Happy / Boundary / Error / Regression / Characterization] | [name] | [input] | [value or error] | [arithmetic or spec reference] | [bug this catches] |

## Test Code
[complete, runnable test file]

## Verification
- **Command**: [exact command]
- **Result**: [pasted summary line, or "Not run — reason"]

## Coverage Gaps
- [gap] — [risk] — [why not covered]
```

If no findings, write "None found" under Findings and keep the section. Severity uses the shared scale: 🔴 BLOCKER — security hole, data loss/corruption, crash on reachable input, or broken contract; 🟠 MAJOR — real bug or missing validation at a trust boundary; 🟡 MINOR — maintainability, clarity, or robustness issue (dead code, unclear spec); 💭 NIT — style.

`template.md` mirrors this format. A worked example is in `examples/example.txt` (if installed).
