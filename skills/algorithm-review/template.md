# Algorithm Review: [scope]

**Scale**: [n, m, call frequency per function — "from input" or "assumed: …"]
**Verdict**: [Optimize now / Optimize if scale grows / Fine as-is] — [one sentence]

## Findings

### [🔴/🟠/🟡/💭] [Short title]
**Location**: [file:line–line or function name]
**Signal**: [the pattern that triggered this finding]
**Current**: [O(...) — which term dominates, with operation count at stated scale]
**Proposed**: [O(...) — technique name]

Before:
[original code, or the relevant lines]

After:
[rewrite]

**Edge cases checked**: [duplicates, missing keys, empty input, ordering/ties, … — and how each is preserved; assumptions stated]
**Equivalence**: [what was run — edge cases + N randomized inputs, old vs new, all equal] or [NOT verified — harness below]
**Behavior changes / questions**: [None, or what the user must decide]

## Fine As-Is
- [function/location] — [why no change is needed]

## Top Priorities
1. [Most impactful change]
2. [...]
