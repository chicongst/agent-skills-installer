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
