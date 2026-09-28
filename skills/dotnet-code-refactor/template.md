## Refactor Plan
**Files:** `[path/to/File.cs]`
**Smell → refactoring:** [smell → refactoring]
**Risk:** [SAFE / RISKY / DANGEROUS]
**Safety net:** [✅ sufficient / ⚠️ weak — adding characterization tests / ❌ none — adding]
**Steps:** 1. [atomic, builds and passes on its own] 2. [next step] …

# Refactor Report — [file/feature]
**Smell → refactoring:** [smell → refactoring] **Risk:** [SAFE / RISKY / DANGEROUS]
## Changes
- [one line per change/file]
## Verification
- Build: [✅ / ❌] (warnings: before [N] → after [N])   Tests: [✅ / ❌] [X] passed ([Y] characterization tests added)
- Behavior evidence: [input → same output before and after]
## Deliberately not changed
- [tempting cleanups or deferred smells, and why]
## Behavior changes recommended (not applied)
- [🔴 BLOCKER / 🟠 MAJOR / 🟡 MINOR / 💭 NIT] [title] — `[file:line]` — [problem] → [proposed separate change]
