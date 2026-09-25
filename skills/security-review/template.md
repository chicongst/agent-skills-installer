# Security Review — [component / files / change]

**Scope:** [files and entry points reviewed]
**Findings:** 🔴 [n] · 🟠 [n] · 🟡 [n] · 💭 [n]
**Verdict:** [REQUEST CHANGES / APPROVE WITH COMMENTS / APPROVE]

## Summary
[2–4 sentences: what the code does, the most serious weakness, why this verdict.]

## Trust boundaries and data flows
| Entry point | Untrusted input | Reaches (sink / asset) | Controls present |
|---|---|---|---|
| [route / consumer] | [fields] | [SQL, response, log, …] | [auth, validation, none] |

## Findings

### 🔴 BLOCKER
#### [B1] [Short title] [verified]
**Location:** `path/file.ext:L10-L12`
**Weakness:** [class, optional CWE ID]
**Root cause:** [what the code does wrong, source → sink]
**Impact:** [what an untrusted actor could read, change, or break]
**Exploitability:** [High / Medium / Low — who can trigger it, preconditions]
**Fix:**
```[lang]
[minimal snippet]
```
**Regression test:** [test name — what it asserts]

### 🟠 MAJOR
[Same fields, IDs M1, M2…]

### 🟡 MINOR
[Same fields; Fix may be one line; Regression test optional. IDs m1, m2…]

### 💭 NIT
- `path/file.ext:L5` — [one line]

## Regression tests
```[lang]
[runnable tests in the project's framework, one per BLOCKER/MAJOR where feasible]
```

## Questions
- [Question, and which finding or severity it could change]

## Checked OK
- [Checklist area]: [why it's fine]

## Not assessed
- [Checklist area]: [what was missing to assess it]

## What's good
- [Specific control worth keeping]
