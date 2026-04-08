---
name: refactor
description: Use when user asks to refactor, clean up, simplify, or restructure code. Also use when code has unnecessary complexity, deep nesting, premature abstractions, or scattered related logic.
---

# Refactoring Specialist

Refactoring means changing code structure without changing behavior. Goal: **simpler, clearer, easier to change** — not more files or more abstractions.

## Core Principle

**Simplify, don't just split.** Extracting small functions is not always good refactoring. Sometimes code is simpler when kept in one place.

---

## ANTI-PATTERNS: Common Refactoring Mistakes

### 1. Extract everything into helpers

```
❌ WRONG: Extract a query into a separate helper
// helpers/getUserQuery.ts
export const buildGetUserQuery = (id) => db.query('SELECT * FROM users WHERE id = ?', [id])

// service.ts
import { buildGetUserQuery } from './helpers/getUserQuery'
const user = await buildGetUserQuery(id)

✅ RIGHT: Query belongs where it is used
// service.ts
const user = await db.query('SELECT * FROM users WHERE id = ?', [id])
```

**Rule: Do not extract queries, config access, or one-time logic into helpers.** Only extract when that logic is genuinely used in 3+ places AND has a clear contract.

### 2. Premature abstraction

```
❌ WRONG: Create abstraction for a single use case
class NotificationStrategy { ... }
class EmailNotification extends NotificationStrategy { ... }
// Only email exists — no SMS or push yet

✅ RIGHT: Write directly, refactor when a third use case appears
await sendEmail(user.email, subject, body)
```

### 3. Over-splitting functions into tiny pieces

```
❌ WRONG: 3-line logic split into 3 separate functions
const isValid = validateAge(age) && validateName(name) && checkDuplicate(email)

// when validateAge is just: return age >= 18 && age <= 120
// when validateName is just: return name.length > 0
// → Loses context, requires jumping across 3 files to understand 1 line

✅ RIGHT: Inline simple logic
const isValid = (age >= 18 && age <= 120) && name.length > 0 && !existingEmails.has(email)
```

### 4. Wrappers that add no value

```
❌ WRONG: Wrap a library just to wrap it
// utils/logger.ts
export const log = (msg) => console.log(msg)  // Adds nothing

✅ RIGHT: Only wrap when adding real behavior
// Valuable wrapper: adds structured logging, correlation ID
export const log = (msg, ctx) => logger.info({ msg, requestId: ctx.requestId, timestamp: Date.now() })
```

---

## WHEN TO REFACTOR (and when not to)

### Refactor when

| Signal | Action |
|--------|--------|
| Function > 50 lines AND does multiple distinct things | Extract by responsibility, not by line count |
| Logic duplicated in 3+ places with the same contract | Extract shared function |
| Deep nesting (> 3 levels) | Early return, guard clause, flatten |
| Complex conditional | Extract into a well-named boolean variable (not a function) |
| God class / God function | Split by domain boundary |
| Dead code | Delete entirely — do not comment out |
| Confusing names | Rename to clarify intent |

### Do NOT refactor when

| Signal | Reason |
|--------|--------|
| Short function that "could be split" | If readable in one pass → leave it |
| Query / DB access | Keep close to where it's used — don't extract to helper |
| Logic used in only one place | Inline is better than abstract |
| Working code nobody needs to change | "If it ain't broke, don't refactor it" |
| Style preference (tabs vs spaces, quotes) | That's formatting, not refactoring |

---

## REFACTORING MOVES (prioritized by impact)

### Tier 1: Almost always good
- **Rename** — clearer intent
- **Early return / Guard clause** — reduce nesting
- **Remove dead code** — delete entirely, don't comment out
- **Replace magic numbers** — named constant
- **Inline trivial function** — remove unnecessary indirection

### Tier 2: Good in the right context
- **Extract Method** — ONLY when function clearly does multiple distinct things
- **Extract Variable** — complex expression → named variable
- **Introduce Parameter Object** — when > 4 params AND they always travel together
- **Replace inheritance with composition** — when hierarchy > 2 levels

### Tier 3: Be careful — easy to over-engineer
- **Strategy/Factory pattern** — ONLY when there are 3+ real variants
- **Extract shared utility** — ONLY when used in 3+ places with the same contract
- **Introduce interface/abstraction** — ONLY when there is a real need to swap implementations

---

## PROCESS

1. **Read the code** — understand full context before changing anything
2. **Identify real smells** — distinguish real problems from style preferences
3. **Check test coverage** — do not refactor untested code; write tests first
4. **Small steps** — each commit is one refactoring move; run tests after each step
5. **Verify** — confirm behavior is unchanged and the code is genuinely simpler

## OUTPUT FORMAT

```
## Refactoring Plan: [Component]

### Issues found
| Smell | File:Line | Severity |
|-------|-----------|----------|
| [Specific description] | [location] | [High/Medium/Low] |

### Refactoring steps (in order)
1. **[Move type]**: [Description]
   - Why: [Specific reason — not just "cleaner"]
   - Before → After: [code sketch]
   - Test to verify: [which test confirms behavior is preserved]

### Not refactoring
- [List code that might seem extractable but SHOULD NOT be, and why]

### Risk
- [Risks and mitigations]
```

## Iron Rules

1. **Every refactoring move must have a specific reason** — "cleaner" is not a reason
2. **Three similar lines beat one premature abstraction** — wait for the third use case
3. **Queries, config, one-time logic: do NOT extract to helper** — keep close to usage
4. **Inline > Extract when a function is used in only one place and is < 5 lines**
5. **Do not create new files unless truly necessary** — fewer files = less complexity
6. **Test first, refactor second** — no tests means write tests first; that IS part of refactoring
