---
name: fix-bug
description: Use when user reports a bug, pastes an error message, says code isn't working, asks why something fails, or requests debugging help. Use even for vague reports like "fix this", "not working", "why is this failing", or any stack trace. Ensures deep context analysis before proposing a fix instead of guessing.
---

# Fix Bug — Deep Debugger

**Never fix immediately.** Always go through the analysis process first. A rushed fix can create more bugs than it solves.

---

## PHASE 1: Gather Context (REQUIRED)

Before proposing any fix, complete the following:

### 1.1 Define bug scope

- Which layer is affected? (UI / API / Database / External Service / Infrastructure)
- Which feature or module?
- Is it reproducible? Under what conditions?
- Frequency: always or intermittent?

### 1.2 Trace the data flow

- What is the input? Format and source?
- Which functions or modules does data flow through?
- Any transformations between steps?
- Where does expected output diverge from actual output?

### 1.3 Analyze dependencies

- Which files or modules are directly involved?
- Any shared state? (global variables, context, store, cache)
- External dependencies: APIs, databases, third-party services?
- Environment variables or config that could affect behavior?

### 1.4 Check history

- Did this code ever work correctly?
- Any recent changes? (commits, deploys, config changes)
- Any packages or dependencies recently updated?
- Did the bug appear after a specific event?

### 1.5 Consider edge cases

- What happens with null / undefined / empty data?
- What about unexpectedly large or malformed data?
- Could a race condition occur?
- Timeouts or network issues?

---

## PHASE 2: Ask the User (When Information Is Missing)

If critical information is missing, **use the `AskUserQuestion` tool** to ask the user — do not ask in plain text. The tool renders as a UI with buttons or options for faster responses.

Group up to 4 questions per call. Prioritize the most important ones first.

### Sample questions by category

**About the error/symptom:**
- "When does the bug occur?" → options: `Every time` / `Only in some cases` / `First time seeing it`
- "Is there a stack trace?" → options: `Yes, here it is` (+ Other) / `No`

**About environment:**
- "Which environment?" → options: `Local` / `Staging` / `Production` / `All`
- "Did the bug appear after a change?" → options: `New deploy` / `Dependency update` / `Config change` / `Unknown`

**About history:**
- "Did this code ever work correctly?" → options: `Yes, it worked before` / `Never worked` / `Not sure`
- "Have you tried any fixes?" → options: `No attempts yet` / `Tried but failed` / `Partially fixed`

**About business logic:**
- "What is the expected behavior?" → use `Other` for free-text if no options fit

---

## PHASE 3: Root Cause Analysis

Once sufficient information is gathered, analyze using the following framework:

### 3.1 Distinguish Symptom vs Root Cause

| Symptom | Root Cause |
|---------|------------|
| API returns 500 | Null pointer in service layer |
| UI doesn't render | State not updated correctly |
| Wrong data returned | Transform logic error |

Always dig down to the root cause — never fix the symptom.

### 3.2 Apply 5 Whys

Keep asking "Why?" until reaching the underlying cause:

```
Bug: API timeout
→ Why? Slow database query
→ Why? Missing index
→ Why? Schema not designed for this access pattern
→ Root cause: Add index + review schema design
```

### 3.3 Common bug categories to check

- **Logic errors**: Wrong condition, off-by-one, wrong operator
- **State management**: Race conditions, stale state, memory leaks
- **Type errors**: Null/undefined, type coercion, unexpected format
- **Async issues**: Missing await, unhandled promise rejection
- **Integration bugs**: API contract mismatch, serialization issues
- **Environment bugs**: Config differences, version mismatches

---

## PHASE 4: Propose a Fix

### 4.1 Pre-fix checklist

- [ ] Root cause understood — not just the symptom
- [ ] Data flow traced from input to error point
- [ ] Edge cases considered
- [ ] Fix does not break other functionality
- [ ] Backward compatibility considered
- [ ] Any remaining assumptions clearly noted

### 4.2 Fix output format

```
🔍 ANALYSIS
- Bug and observed symptom
- Trace from input to error point
- Files and functions reviewed

🎯 ROOT CAUSE
- Underlying cause of the bug
- Why it produces that symptom

🛠️ PROPOSED FIX
- Specific code fix with explanation
- Why this fix addresses the root cause

⚠️ WARNINGS
- Possible side effects
- Other places to check
- Breaking changes if any

✅ VERIFICATION
- How to test that the fix works
- Edge cases to test
- Regression tests to add

❓ STILL UNKNOWN (if any)
- Information that is still unclear
- Assumptions being made
- Questions for the user to confirm
```

---

## PHASE 5: Verify & Follow-up

### 5.1 Suggest test cases

```
Test 1: Happy path — [description]
Test 2: Edge case — null/empty input
Test 3: Edge case — concurrent requests
Test 4: Regression — [related feature]
```

### 5.2 Monitoring suggestions (when applicable)

- Logs to add for ongoing monitoring
- Metrics to track
- Alerts to set up

---

## Special Rules

### When reading code from files

1. Read the specified file first
2. Identify imports and dependencies
3. Find and read related files
4. Trace the call chain from the entry point

### When given an error message

1. Parse the error type and location
2. Find the file and line number mentioned
3. Trace back from the error point to understand context
4. Check the conditions that led to the error

### When the bug is intermittent

1. Ask about timing and frequency
2. Check for race conditions
3. Check caching issues
4. Check external dependencies (network, third-party APIs)

### When information is insufficient

**Do NOT guess.** Instead:
1. List what is already known
2. List what additional information is needed
3. Ask the user specific questions
4. Suggest steps to gather more info (logs, debugging steps)

---

## Output Confidence Levels

When proposing a fix, indicate the confidence level:

- **🟢 HIGH**: Fully traced, reproduced, root cause is clear
- **🟡 MEDIUM**: Some assumptions made — user confirmation needed
- **🔴 LOW**: Significant information missing — this is a hypothesis only

If confidence is MEDIUM or LOW, always include clarifying questions.
