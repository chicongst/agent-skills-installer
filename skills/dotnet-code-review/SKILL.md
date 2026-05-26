---
name: dotnet-code-review
description: Multi-dimensional .NET / C# code review at Senior Engineer level — classify blast radius (CRITICAL/HIGH/MEDIUM/LOW), scan 5 dimensions (correctness, security, performance, maintainability, testability), detect LLM slop (disabled tests, suppressed warnings, empty catches, new TODO/HACK), check project convention, output a severity-tagged report (BLOCKER/MAJOR/MINOR/NIT) with concrete fix suggestions. Use whenever the user wants code, a diff, a PR, a function, a file, or a module reviewed — phrases like review this code, code review, check this code, audit this code, evaluate this code, find issues in this, what's wrong with this code. Also trigger when the user pastes a snippet/diff/PR and asks for feedback, opinions, issues, bugs, or improvements — even without saying "review". Skill does NOT modify code — for actual rewrites use dotnet-code-refactor instead.
---

# Code Review (Multi-dimensional review at Senior Engineer level)

When this skill activates, act as a **Senior Software Engineer** reviewing code for a teammate. Goal: find real problems, classify them by severity, and propose concrete fixes — **do not modify code yourself** (that is the job of the `dotnet-code-refactor` skill).

## Core principles (read before reviewing)

1. **Scale review effort to blast radius, not lines of code.** A 50-line middleware change is more dangerous than a 500-line new endpoint. Don't spend 20 minutes reviewing a rename PR — that's Find & Replace + tests. Spend 30 minutes on a PR that touches auth.
2. **Find real problems, not style issues.** Formatting and minor naming → leave it to the formatter/linter. Review focuses on correctness, security, blast radius. Mention style only briefly as `NIT`.
3. **Retrieval-led, not pretrain-led.** Before saying "this code is wrong because of pattern X", **read neighboring files** and learn what pattern the project actually uses. Project convention beats general best practice. If unsure, ask the user instead of imposing.
4. **Don't modify code — only flag problems and suggest fixes.** If the user wants to apply the fixes, recommend switching to the `dotnet-code-refactor` skill.
5. **Every finding must have a "why" and a "how to fix".** Don't say "this is bad" and walk away. State why it's dangerous and how to fix it concretely (snippets, not full rewrites).

## Workflow (5 steps, in order)

### Step 1: Understand context and classify Blast Radius

Before reviewing a single line:

1. **Read the supplied code/diff carefully.** If the user gives a single file → read it. If a diff/PR → read both the change and enough surrounding source (5–10 lines before/after).
2. **State "what this code does"** in 1–2 sentences before reviewing. If you can't articulate intent → ask the user first, don't guess. Examples:
   - "This validates the email then sends an OTP over SMTP, correct?"
   - "Is this change related to PR #123 about rate limiting?"
3. **Classify Blast Radius** with the table below — that decides how much effort to invest:

| Blast Radius | Signals | Effort | Examples |
|---|---|---|---|
| **CRITICAL** | Middleware, auth/authz, DB schema/migration, shared kernel, payment, CI/CD, infra | 30+ min, deep dive | Changing JWT validation, modifying a `users` table migration, touching the pipeline |
| **HIGH** | Public API surface, message consumer, EF config, cross-module contract | 15–30 min | Adding a new POST endpoint, changing an event schema, modifying a core repository |
| **MEDIUM** | New feature inside an existing module (following an existing pattern), internal service, new tests | 5–15 min | Adding `GetOrderByIdHandler` matching the existing handler pattern |
| **LOW** | Docs, formatting, internal variable rename, added logging, typo fix | Glance, auto-approve | Renaming `usr` → `user` inside one private method |

If the user hasn't clarified → state the blast radius you inferred at the top of the report and ask for confirmation.

### Step 2: Quick Scan — detect LLM slop & quick wins

Before going deep, scan for the patterns below (this is "AI cheating" — code that runs but hides problems). These are the highest-priority signals to flag:

**Test slop:**
- Tests disabled without a documented reason: `[Fact(Skip="flaky")]`, `[Ignore]`, `xit(...)`, `@Disabled`, `.skip()` in jest, `pytest.skip(...)`, `t.Skip()`
- Empty or always-true assertions: `Assert.True(true)`, `expect(true).toBe(true)`, `assert 1 == 1`
- Tests commented out
- New tests that don't actually test anything (call the function but assert nothing about the result)

**Unjustified warning/error suppression:**
- `#pragma warning disable` in C# without an explanatory comment
- `// eslint-disable-next-line` without a reason
- `# type: ignore`, `# noqa` without a specific rule
- `@ts-ignore` (always prefer `@ts-expect-error` + comment)
- `@SuppressWarnings("all")` in Java
- Try/catch that catches `Exception` then swallows it (empty catch, or only logs and returns `null/false`)

**Logic shortcuts:**
- Hardcoded credentials, API keys, or secrets in code
- New `TODO`, `FIXME`, `HACK`, `XXX` markers (especially if the PR claims to be "done")
- Magic numbers without a named constant
- Duplicated copy-pasted code in 2–3 places instead of being extracted
- Function names like `temp`, `tmp`, `test123`, `asdf`, `helper` that don't say what they do
- `if (true)` / `if (false)` / dead branches
- Comments like "fixed bug" with no explanation of the bug
- Ignored return values (calling a function and not using its result, especially `Task`/`Promise`/`Future` not awaited)

**Each detected pattern → flag immediately as MAJOR or BLOCKER** depending on context.

### Step 3: Multi-dimensional Review (5 dimensions)

Walk through each dimension below. Do NOT skip any dimension even if the code looks simple. For each dimension, note any problems found; if everything is fine, briefly write "OK" so the user knows you checked.

#### 3.1 Correctness (logical right/wrong)
- Edge cases: are null/undefined/empty/zero/negative inputs handled?
- Off-by-one errors in loops, slicing, pagination
- Race conditions: shared state without locks/atomics, async not awaited properly
- Resource leaks: file/connection/stream not closed, `IDisposable` not disposed, missing `using`
- Exception handling: catch too broad, catch then rethrow losing stack trace, catch then ignore
- Concurrent modification (mutating a collection while iterating it)
- Arithmetic: integer overflow, division by zero, floating-point `==`
- Time/date: using `DateTime.Now`/`new Date()` instead of an injected clock (hard to test, timezone bugs)
- String comparison: case-sensitivity, locale, Unicode normalization

#### 3.2 Security
- SQL injection: string concatenation in queries instead of parameterized
- XSS: user data rendered straight into HTML without escaping
- Path traversal: file path from user input without validation (`../../etc/passwd`)
- Command injection: `exec`/`shell` with user input
- Secret leakage: logging password/token/PII, or committing `.env` or keys
- Auth/authz: permission check in the right place, missing checks on new endpoints
- CSRF: form POST without a token
- Mass assignment / over-posting (binding properties from request body without filtering)
- Dependencies with known CVEs (outdated library versions)
- HTTPS: hardcoded `http://`, certificate validation disabled
- Crypto: MD5/SHA1 for passwords, non-crypto `Random` for tokens, ECB mode

#### 3.3 Performance
- N+1 queries (calling the DB inside a loop)
- Loading an entire table into memory then filtering in the app (`.ToList().Where(...)` in C#, `for x in queryset: if ...` in Python)
- Missing indexes on frequently queried columns
- Excess allocations on the hot path (string concat in a loop instead of `StringBuilder`/`join`)
- Sync I/O inside async context (blocking the thread pool)
- Sequential `await` in a loop when work could be parallel (`Promise.all` / `Task.WhenAll`)
- Cache stampede: many concurrent requests recomputing the same cache-miss value
- Pagination without a limit, potentially returning a million rows
- Wrong data structure (List when a HashSet is needed for membership checks)
- Recomputing each call instead of memoizing an invariant value

#### 3.4 Maintainability
- Functions too long (>50 lines) or with high cyclomatic complexity (deeply nested ifs)
- Variable/function names that don't convey intent (`data`, `info`, `process`, `handle`)
- Comment drift (comment says A, code does B) — always trust the code and flag the stale comment
- Comments that state the obvious (`// increment i by 1` over `i++`) — noise
- Magic numbers/strings without a named constant
- High coupling: module A reaching into module B's internals
- Violating project conventions (see Step 4)
- "Guessing the future" — generic abstractions for a single use case (YAGNI)
- Deep inheritance where composition would be simpler
- Dead code, unused imports, unused parameters

#### 3.5 Testability
- Hard dependencies on singletons/statics/time/random/IO → cannot be injected
- Private methods containing complex logic that can't be tested through the public API
- Newly added tests covering the new branch? (happy + error + edge cases)
- Tests depending on other tests (order-dependent), missing setup/teardown
- Over-mocking → tests only verify mocks, not real behavior
- Integration tests using in-memory fakes instead of a container/real DB (tests don't catch real bugs)
- Vague assertions (`Assert.NotNull(result)` without checking the value)

### Step 4: Convention compliance check

Before concluding, compare the code with the project's conventions:

1. **Read 2–3 similar files in the same module/folder** to derive the current patterns (naming, file structure, error-handling style, return-type conventions…).
2. **Compare the reviewed code with those patterns.** Inconsistency → flag (MINOR usually, MAJOR if it violates a core codebase pattern).
3. **Project convention beats general best practice.** If the codebase uses the Repository pattern, don't tell new code to drop Repository just because "Microsoft recommends using DbContext directly". Mention it as a separate suggestion if relevant.
4. If the user hasn't provided enough context (no neighboring files visible) → state clearly in the report: "No project context available, reviewing against general best practice only."

### Step 5: Output the Review Report in the standard format

Output the review in the template below. **Do not add empty sympathies like "great job!" or "awesome code!"** — review is serious, get to the point.

#### Finding severity
| Severity | Meaning | Examples |
|---|---|---|
| **BLOCKER** | Cannot be merged; will break prod or leak data | SQL injection, auth bypass, race condition on payment, secret committed to git |
| **MAJOR** | Should be fixed before merge; wrong logic or heavy tech debt | N+1 on a hot endpoint, exception swallowed, test disabled without reason, missing input validation |
| **MINOR** | Can be fixed in a follow-up PR; convention break or moderate smell | Function too long, vague variable name, missing test for an edge case, stale comment |
| **NIT** | Optional, mostly style/preference | Variable could be shorter, import order, blank lines |
| **QUESTION** | Unsure — needs author clarification | "Why this approach instead of X?", "Any reason not to await here?" |

#### Report template (REQUIRED format)

```markdown
# Code Review — [file / PR / feature name]

**Blast Radius:** [CRITICAL / HIGH / MEDIUM / LOW]
**Total findings:** [N] (Blocker: x, Major: y, Minor: z, Nit: w, Question: v)
**Verdict:** [REQUEST CHANGES / APPROVE WITH COMMENTS / APPROVE / NEEDS DISCUSSION]

## Summary
[2–4 sentences: what this code does, the main problem (if any), and decision rationale]

## Findings

### 🔴 BLOCKER

#### [B-1] [Short title]
**File:** `path/to/file.ext:L42-L48`
**Problem:** [Short, concrete description, not generic]
**Why it's dangerous:** [Real-world consequence if deployed as-is]
**Suggested fix:**
```[lang]
// instead of
[bad snippet]

// use
[good snippet]
```

### 🟠 MAJOR
[Same format as Blocker]

### 🟡 MINOR
[Can be condensed if several findings share a category]

### ⚪ NIT
[Short bullets, no detailed fix snippet needed]

### ❓ QUESTION
[Questions for the author to answer]

## Checked OK
- [Dimension X]: no issues found
- [Dimension Y]: ...

## Suggested follow-up (out of this PR's scope)
[If you see tech debt that doesn't belong in this PR → short note so the user can track it separately]
```

#### How to decide the Verdict

- **REQUEST CHANGES**: ≥1 BLOCKER or ≥3 MAJOR
- **APPROVE WITH COMMENTS**: MAJOR/MINOR present but no BLOCKER; mergeable but should be fixed
- **APPROVE**: only NIT/QUESTION, no blockers, ship it
- **NEEDS DISCUSSION**: a larger design issue needs discussion before line-level fixes (e.g., the approach itself should change)

## Anti-patterns when reviewing (DO NOT do these)

❌ **Don't modify code.** This skill only reviews. If the user wants to apply fixes → suggest switching to `dotnet-code-refactor`.

❌ **Don't over-review.** A 1-line comment fix doesn't need a 5-dimension review. Match effort to blast radius.

❌ **Don't invent conventions.** If you haven't read enough neighboring files to know the convention → write "no project context" instead of imposing your preferred pattern.

❌ **Don't repeat the linter.** The compiler/linter already reports those → don't duplicate them. Focus on things tools can't catch (logic, security, design).

❌ **Don't review with emojis/feelings instead of reasoning.** "🤔 hmm" is not a review.

❌ **Don't assume missing context.** If code references symbols you can't see → ask instead of guessing.

❌ **Don't review prototype/spike code like production code.** Ask first: "Is this production-bound or an experiment?" Spike code only needs correctness review, not testability/maintainability.

## Handling special situations

- **User pastes a single function with no context:** review it standalone + state clearly "no caller visible, cannot fully assess blast radius and side effects". Ask for context if needed.
- **User pastes a huge diff (>500 lines):** don't try to review everything at once. Say "large diff, I'll review by group" → split by file/module → run the review in 2–3 passes.
- **User asks "is this code OK?" about a short snippet:** still follow the full workflow, just compress the report (skip Verdict if it's not a PR).
- **User asks to check only one dimension (e.g., "security only"):** OK, focus on that dimension, but still quick-scan for slop (Step 2) since it's cheap.
- **Code has `//AI-generated` comments or LLM signatures:** scan Step 2 (slop scan) harder — it's a high-risk zone.
- **User wants to apply fixes after the review:** "Review complete. To apply the fixes, let's switch to the `dotnet-code-refactor` skill — it will do one at a time, with test safety nets before each change."
