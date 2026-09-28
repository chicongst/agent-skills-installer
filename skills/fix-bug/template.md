## Bug: [one-line title]
**Confidence**: High / Medium / Low — [why, in one line]

### Symptom
- **Expected**: [...]
- **Actual**: [exact error or wrong value, quoted]
- **Trigger / frequency / environment**: [...]

### Investigation
- Path traced: [entry point → ... → failure point, with file:line]
- Depends on: [shared state, config/env, external calls, concurrency on this path — only what matters]
- History: [relevant commits/changes, or "no recent changes to this path"]
- Reproduction: [command or test + result, or why it could not be reproduced]

### Root cause
[Causal chain with file:line — a fact, not a remedy]

### Fix
[Minimal diff]
**Behavior change for other callers**: [none / what changes]
**Same pattern elsewhere**: [grep command + hits, or "none found"]

### Verification
- [ ] Regression test `[name]` fails before, passes after — [command + result]
- [ ] Original reproduction passes — [result]
- [ ] Surrounding suite passes — [command + result]

### Open questions (Medium/Low only)
- [question or check that would raise confidence]

---

<!-- Fast path (obvious bug): use only these parts -->

## Bug: [one-line title]
**Confidence**: High — [one-line reason]

### Root cause
[Causal chain with file:line — a fact, not a remedy]

### Fix
[Minimal diff]

### Verification
[Command run + result, and regression test name — or why the command itself catches a recurrence]
