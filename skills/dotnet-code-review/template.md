# .NET Code Review — [file / feature]

**Blast radius:** CRITICAL | HIGH | MEDIUM | LOW
**Findings:** Blocker x · Major y · Minor z · Nit w
**Verdict:** REQUEST CHANGES | NEEDS DISCUSSION | APPROVE WITH COMMENTS | APPROVE

## Summary
[2–4 sentences: what the code does, the main risk, why this verdict]

## Findings
### 🔴 BLOCKER
#### [B-1] [Short title]
**Location:** `path/File.cs:42-48`
**Problem:** [concrete defect]
**Impact:** [what happens in production]
**Fix:**
```csharp
// before
...
// after
...
```
### 🟠 MAJOR
[same fields, M-1…]
### 🟡 MINOR
[same fields; may group findings sharing a cause]
### 💭 NIT
- [one line each]

## Questions
- [things only the author can answer]

## Checked OK
- [section]: [what was verified]

## Follow-up (out of scope)
- [tech debt noticed but unrelated to this change]
