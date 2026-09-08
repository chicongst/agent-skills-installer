---
name: dotnet-code-refactor
description: Safely refactor .NET / C# code at Senior Engineer level — diagnose code smells, classify risk (SAFE/RISKY/DANGEROUS), check the test safety net (or add characterization tests first), apply smallest-change-at-a-time for one smell, preserve behavior, match project convention. Use when the code being rewritten, restructured, cleaned up, or simplified is C#, .NET, or ASP.NET, and after a `dotnet-code-review` when the user says "apply the fixes". For any other language use `refactor`. DOES modify code (unlike `dotnet-code-review`, which only inspects).
---

# Code Refactor (Safe code improvement at Senior Engineer level)

When this skill activates, act as a **Senior Software Engineer** refactoring a module that other people are using. Goal: improve code quality **without changing behavior**, **without breaking tests**, and **without bundling multiple changes into a single step**.

This skill is different from `dotnet-code-review`: here you **actually modify the code**, not just point out problems. It's also different from greenfield code generation: this is **editing live code already in use**, which is much riskier.

## Core principles (read before touching code)

1. **Refactoring does not change behavior.** That's the definition. If the output or behavior changes after refactoring — that's not a refactor, that's a rewrite (treat it as a feature change, with a spec and new tests). When unsure what the old behavior is → don't guess, write a characterization test first.
2. **Smallest possible change, one smell at a time.** Don't combine "rename + extract method + change return type" into one commit. Each refactoring is a standalone step: test passes, then move to the next. Reason: if something breaks, it's easy to locate.
3. **Don't refactor and add a feature in the same change.** Split the work: refactor first (behavior identical, tests green) → commit → add the feature → commit. Mixing them makes review impossible to split and debugging impossible to bisect.
4. **Project convention beats general best practice.** If the codebase uses `_camelCase` for private fields, don't switch to `camelCase` just because "Microsoft recommends it". Read 2–3 neighboring files and follow what they do.
5. **Tests are a mandatory safety net.** No tests → no refactoring (or write characterization tests first). Tests exist but are weak (mock everything, assert nothing) → treat as no tests.
6. **High risk and no way to reduce it → stop and ask the user.** Don't refactor authentication, payment, or migrations by yourself.

## Workflow (6 steps, in order, no skipping)

### Step 1: Diagnose — identify the smell and the intent

Before changing a single line:

1. **Read the current code carefully** and understand what it does (like Step 1 of code-review). If you can't articulate intent → ask the user, don't guess.
2. **List the code smells you found.** Classify them with the table below:

| Smell | Signal | Matching refactoring |
|---|---|---|
| **Long Method** | Function >50 lines, doing several things | Extract Method, Replace Temp with Query |
| **Large Class** | Class >300 lines, multiple responsibilities | Extract Class, Extract Subclass |
| **Long Parameter List** | >4–5 parameters | Introduce Parameter Object, Preserve Whole Object |
| **Duplicate Code** | Same logic in 2–3 places | Extract Method, Pull Up Method, Form Template Method |
| **Feature Envy** | Method A uses class B's properties more than its own | Move Method |
| **Data Clumps** | Several fields always travel together (firstName, lastName, dob) | Extract Class / Record |
| **Primitive Obsession** | Using string/int for a domain concept (email is a string, money is a decimal) | Replace Primitive with Value Object |
| **Switch Statements** | Large switches on type, repeated in many places | Replace Conditional with Polymorphism, Replace Type Code with Subclass |
| **Lazy Class** | Class with too little behavior | Inline Class |
| **Speculative Generality** | Abstraction with only one use case | Inline Class, Collapse Hierarchy |
| **Temporary Field** | Field used only inside a few methods, null otherwise | Extract Class, Introduce Null Object |
| **Message Chains** | `a.getB().getC().getD().doIt()` | Hide Delegate |
| **Middle Man** | Class only delegates to another class | Remove Middle Man |
| **Inappropriate Intimacy** | Two classes know too much about each other's privates | Move Method, Extract Class, Change Bidirectional → Unidirectional |
| **Comments** | Long comments explaining "what the code does" | Extract Method with a clear name; let the code self-document |
| **Mysterious Name** | `data`, `tmp`, `handle`, `process` | Rename |
| **Magic Number/String** | Strange numbers/strings scattered around | Replace Magic Literal with Constant |
| **Deeply Nested Conditional** | if-in-if-in-if 4–5 levels deep | Decompose Conditional, Guard Clauses, Replace Nested Conditional with Guard Clauses |

3. **Agree with the user on which smells to fix in this session.** Don't fix everything yourself. If the user says "refactor this file", list the smells you found + propose the top 2–3 → ask the user to pick.

### Step 2: Classify Risk — decide whether to touch it

Each refactoring carries different risk. Classify before changing anything:

| Risk Level | Description | Handling |
|---|---|---|
| **SAFE** | Tool-assisted, behavior provably unchanged | Proceed, no extra safety tests needed (existing tests suffice) |
| **RISKY** | Requires reading/understanding logic, easy to subtly break | MANDATORY safety tests before the change; verify with the test suite after |
| **DANGEROUS** | Touches auth/payment/concurrency/DB schema/public API | REQUIRE USER CONFIRMATION first. Need strong integration tests + rollback plan |

**SAFE refactorings (usually):**
- Rename (local variable, private method, private field) via IDE
- Extract Method from a well-defined block (clear inputs/outputs)
- Inline a local variable used only once
- Reorder methods within a file
- Convert anonymous → named function
- Format code (via the formatter)
- Add type annotations for obvious variables/return types

**RISKY refactorings:**
- Rename a public/exported symbol (affects callers — find them first)
- Extract Class
- Move Method/Field across classes
- Replace Conditional with Polymorphism
- Introduce Parameter Object
- Change exception type / error code
- Change data structure (List → Dictionary…)
- Replace an interface implementation
- Refactor async/concurrent code (locks, channels, await patterns)

**DANGEROUS refactorings (must escalate):**
- Touching authentication / authorization logic
- Touching payment / billing / financial calculation
- Modifying DB schema, migration, or hot-path queries
- Refactoring locks / transactions / concurrency primitives
- Changing a public API contract (signature, response shape, status code)
- Refactoring a message queue consumer (risk of double-process / lost message)
- Touching CI/CD pipelines or deployment scripts
- Modifying security boundaries (input validation, sanitization)

**Rule:** if the refactoring falls into DANGEROUS → STOP, tell the user: "This refactor touches [X], the risk is high. I suggest [approach]. Do you want me to proceed, or should I break it down further?"

### Step 3: Check the Test Safety Net

Refactoring without tests = gambling. Check before changing:

1. **Find tests for the code you'll refactor.** Search the test files by the project's convention: `*.test.*`, `*Tests.cs`, `test_*.py`, etc.
2. **Assess test quality:**
   - ✅ Tests cover main behavior (happy + error + edge cases) → safety net is sufficient
   - ⚠️ Tests exist but are weak (only check method-was-called, mock everything, vague assertions) → treat as no tests
   - ❌ No tests → write characterization tests first
3. **If the safety net is insufficient:**

   a. **For RISKY/DANGEROUS refactors → write characterization tests first.** A characterization test "records the current behavior" (including bugs, if any) before refactoring. Purpose: if the refactor changes behavior, the test will fail. How to write:
      ```
      1. Call the current code with concrete inputs
      2. Capture the actual output (including incorrect/buggy output)
      3. Assert that output
      4. Run the test → it passes (because we're asserting actual output)
      5. Refactor → re-run → still passes = behavior unchanged
      ```
      If you discover a bug while writing characterization tests → DO NOT fix the bug in the same refactor commit. Note it down, fix it separately later.

   b. **For SAFE refactors (local rename, small extract method) → may proceed** if the change is simple and lint/compile checks catch the basics. Still note "test coverage is thin" in the report.

4. **Run the existing tests before changing anything** to confirm they pass (baseline). If they fail to start → DO NOT refactor; ask the user whether the tests are already broken.

### Step 4: Plan — write the refactor plan

Before editing, write a short plan for the user:

```markdown
## Refactor Plan

**File:** `path/to/file.ext`
**Smell:** [smell name]
**Refactoring:** [technical refactoring name, e.g. "Extract Method"]
**Risk:** [SAFE / RISKY / DANGEROUS]
**Test safety net:** [✅ sufficient / ⚠️ weak — characterization tests added / ❌ missing — will add]

**Steps:**
1. [Step 1, atomic, independently commit-able]
2. [Step 2 …]
3. [...]

**Expected outcome:** behavior unchanged, [improvement metric, e.g. "80-line function → four 15–25 line functions"]

**Not in scope:** [things NOT being changed in this refactor — e.g. "not fixing bug X even though we noticed it; separate PR"]
```

Wait for user confirmation before going to Step 5 (especially for RISKY/DANGEROUS). For simple SAFE work, you can skip confirmation if the intent is already clear.

### Step 5: Apply — refactor step by step

Rules while editing:

1. **One refactoring at a time.** Don't combine. If the plan has 3 steps, do step 1 → verify → step 2 → verify → step 3.
2. **After each small step → run the tests.** If tests fail → undo that step, investigate, do not continue. If compile-check fails → fix it before moving on.
3. **When renaming:**
   - Local scope → rename directly
   - Public/exported → first find all usages, list them, ensure all are updated, then rename. For cross-team public APIs → consider adding a deprecated alias instead of a hard rename.
4. **When extracting a method:**
   - Name the new function by "what it does", not "how it works". `calculateTax` is better than `loopThroughItems`.
   - The new function must have clear invariants: inputs, outputs, side effects.
   - Don't extract just to reduce line count — it must carry semantic meaning.
5. **When extracting a class:**
   - The new class must have one clear responsibility
   - Don't create a class with one method (that's a function)
   - Be careful with cross-class state mutation
6. **Match the project's formatting conventions** — run the formatter if available (`dotnet format`, `prettier`, `black`, `gofmt`).
7. **Don't delete useful comments.** Comments explaining "why" (intent, edge-case reasoning) → keep. Comments explaining "what" (when the code is already clear) → safe to remove.
8. **Don't upgrade dependencies / change import paths** during a refactor. That's a separate task.

### Step 6: Verify and Report

After refactoring is done:

1. **Re-run the full test suite** (unit + integration, if available). Must pass 100%.
2. **Run the linter/static analyzer** (if the project has one). Must be clean, or at least no worse than before.
3. **Diff before/after** — re-read it as if reviewing your own code. If you spot changes not in the original plan → reconsider whether they're needed or should be reverted.
4. **Output the report using the template:**

```markdown
# Refactor Report — [file/feature name]

**Smell fixed:** [name]
**Refactoring applied:** [technique name]
**Risk level:** [SAFE / RISKY / DANGEROUS]

## Changes
- [One-line summary per change/file]

## Metrics (before → after)
- Lines: [X → Y]
- Cyclomatic complexity: [if measured]
- Function count: [...]
- Test count: [...]

## Test results
- ✅ All [N] tests pass
- [Or: ⚠️ Added [M] characterization tests before refactoring; all pass]

## Behavior verification
- [Concrete: e.g. "Input X → output Y both before and after refactor"]

## NOT included in this refactor
- [Other smells noticed but deferred to a follow-up PR: ...]
- [Bug discovered while writing characterization tests: ...]

## Suggested next refactor
- [What to do next, independent of what was just done]
```

## Common Refactoring Patterns — cheatsheet

### Long Method → Extract Method

```[lang generic]
// BEFORE — one function doing four things
function processOrder(order) {
  // validate
  if (!order.id) throw new Error("missing id");
  if (order.items.length === 0) throw new Error("empty");
  // calculate
  let total = 0;
  for (const item of order.items) total += item.price * item.qty;
  total += total * 0.1; // tax
  // persist
  db.save({ ...order, total });
  // notify
  email.send(order.customerEmail, `Total: ${total}`);
}

// AFTER — four functions, each does one thing
function processOrder(order) {
  validateOrder(order);
  const total = calculateTotal(order);
  saveOrder(order, total);
  notifyCustomer(order.customerEmail, total);
}
```

### Deeply Nested Conditional → Guard Clauses

```[lang generic]
// BEFORE — pyramid of doom
function discount(user, order) {
  if (user) {
    if (user.isPremium) {
      if (order.total > 100) {
        return order.total * 0.2;
      }
    }
  }
  return 0;
}

// AFTER — early returns
function discount(user, order) {
  if (!user) return 0;
  if (!user.isPremium) return 0;
  if (order.total <= 100) return 0;
  return order.total * 0.2;
}
```

### Switch on Type → Polymorphism (when the switch repeats in many places)

```[lang generic]
// BEFORE — switch on type, repeated in 3 places
function area(shape) {
  switch (shape.type) {
    case "circle": return Math.PI * shape.r ** 2;
    case "rect": return shape.w * shape.h;
  }
}
function perimeter(shape) {
  switch (shape.type) {
    case "circle": return 2 * Math.PI * shape.r;
    case "rect": return 2 * (shape.w + shape.h);
  }
}

// AFTER — each shape knows how to compute itself
// Warning: only switch to polymorphism when the switch REPEATS across multiple methods.
// A switch in a single place is usually clearer left alone.
class Circle { area() {...} perimeter() {...} }
class Rect   { area() {...} perimeter() {...} }
```

### Primitive Obsession → Value Object

```[lang generic]
// BEFORE — email is a string everywhere
function sendEmail(to, subject, body) {
  if (!to.includes("@")) throw new Error("invalid");
  // ...
}

// AFTER — Email is its own type, validation in the constructor
class Email {
  constructor(value) {
    if (!value.includes("@")) throw new Error("invalid email: " + value);
    this.value = value;
  }
}
function sendEmail(to: Email, subject, body) { /* no need to re-validate */ }
```

### Magic Number/String → Named Constant

```[lang generic]
// BEFORE
if (user.age >= 18 && order.total > 50000) { ... }

// AFTER
const LEGAL_ADULT_AGE = 18;
const VIP_ORDER_THRESHOLD = 50000;
if (user.age >= LEGAL_ADULT_AGE && order.total > VIP_ORDER_THRESHOLD) { ... }
```

## Anti-patterns when refactoring (DO NOT do these)

❌ **Don't refactor and add a feature in the same change.** Split into two commits/PRs.

❌ **Don't do a "Big Bang refactor".** Don't gut the whole file and rewrite it when the request was "refactor". That's a rewrite — it needs a fresh spec, new tests, and heavier review.

❌ **Don't refactor without tests.** Either write characterization tests first, or stop.

❌ **Don't impose an ideal pattern on a legacy codebase without asking.** Codebases have their own style. Refactor toward the codebase's style, not "best practice from a 2024 blog post".

❌ **Don't assume "user said refactor = go big".** The user may only want a small fix. Plan first, ask for confirmation.

❌ **Don't refactor a file you don't understand.** Read + ask if needed; don't guess intent.

❌ **Don't skip running the tests after a refactor** with the excuse "small change, surely fine". Those small changes are the ones that break things most often.

❌ **Don't refactor a public API without listing callers.** Find all usages, list them, then decide.

❌ **Don't bundle multiple refactorings into one commit.** One commit = one atomic refactoring. Easier to review and revert.

❌ **Don't delete code that "looks dead" without verifying.** Search references before deleting. Dead-looking code may be invoked via reflection / DI / convention-based wiring.

## Special situations

- **User says "refactor this entire file":** don't do it all. Diagnose → list smells → propose the top 3 → ask which to start with. Good refactoring is incremental, not in one shot.

- **User says "optimize performance":** this is NOT pure refactoring. Performance optimization can change behavior (caching, lazy evaluation). Warn the user and propose benchmarking before/after.

- **After refactoring, tests fail and you don't know why:** STOP. Undo the refactor (git reset / revert). Don't "fix the tests to make them pass" — that's self-deception.

- **User gives long code, no tests, no context:** refuse a large refactor. Propose: "This code has no tests; refactoring without a safety net is risky. I suggest two options: (1) I write characterization tests for part X first, then refactor; (2) only do minimal SAFE refactors (rename, small extract method). Which do you prefer?"

- **User says "no tests needed, just refactor":** warn again. If the user insists → state clearly in the report that the refactor was done without tests and behavior may have changed undetected.

- **Refactoring in a PR with merge conflicts / outdated branch:** rebase/merge first, confirm baseline tests pass, then refactor. Don't refactor on top of code that doesn't build.

- **Code is still ugly or reveals deeper smells after refactoring:** OK. Refactoring is incremental. Note: "after Extract Method, class X reveals smell Y — suggest a follow-up refactor in a later PR".

- **User just wants to rename a variable across files:** still follow the short workflow — find all usages, list before modifying, edit, run tests. Don't skip just because "rename is simple".
