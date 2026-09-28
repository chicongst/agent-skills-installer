---
name: document-review
description: "Use when the user wants a strict, high-standard review of a written document — PRD, design doc, RFC, runbook, guideline, process, onboarding doc, README, or any prose — for structure, clarity, consistency, accuracy against the repo, and whether a reader can act on it. Triggers: \"review this document\", \"strict review\", \"document review\", \"review tài liệu\", \"review khó tính\", \"soi tài liệu\", \"review kỹ\". Not for writing or updating the document yourself (use `docs-writer`), reviewing code or a PR (use `code-review` / `pr-review`), or judging an architecture's technical merit rather than how it is written (use `architect`)."
---

# Document Review

Review a document as the reader who has to act on it with no one to ask: find every place where that reader would misunderstand, stall, or do the wrong thing, rank those places, and say exactly what to write instead. Read-only — hand rewrites to `docs-writer` if the user wants them applied.

## Step 0 — Context

- **Source**: read the file, or review the pasted text. Never review from a description of a document.
- **Type** decides what "complete" means: a runbook needs confirm/mitigate/escalate/rollback; a PRD needs goals, non-goals, users, success metrics, and open questions; a design doc needs alternatives and failure modes; a README needs prerequisites, setup, and a way to verify.
- **Audience**: who acts on it and what they already know. If unstated, assume a competent newcomer with no project context and say so in the summary. Tone and depth findings require an audience — without one, don't raise them.
- **Depth follows stakes.** A one-page internal note gets the passes below in minutes, and only findings that would change what the reader does; a runbook, PRD, or public doc gets every pass in full. Don't pad a short document's review with polish nits.

## Review passes (in order)

### 1. Structure
- Purpose in the first few lines? Could the reader tell in 30 seconds whether this document is for them?
- Sections in the order the reader needs them; nothing required is missing for this document type; no duplicated content that can drift.

### 2. Clarity
- Every key term defined at first use; acronyms expanded once.
- Vague words that hide a decision ("soon", "robust", "as needed", "should", "etc.") → ask for the concrete value or rule.
- Marketing language and filler cut; passive voice flagged where it hides *who* acts.

### 3. Consistency and accuracy
- One term per concept throughout ("user" vs "customer" vs "account holder").
- Numbers, names, step counts, and cross-references agree with each other; contradictions between sections are always findings.
- **Check claims you can check.** When the document describes this repo — commands, file paths, env vars, config keys, endpoints, versions — look them up. Run commands only when they are local, read-only, and cost nothing; otherwise mark them "not run". Internal anchors and relative links: verify directly.
- External URLs: don't fetch unless asked; list them as "unverified — confirm manually".
- A claim you can't verify from the document or the repo is flagged as unverified, not assumed right or wrong.

### 4. Actionability
- Walk every procedure step by step as the reader. Any step that can't be executed as written — missing command, missing permission, undefined "verify it looks good" — is a finding.
- Decisions have criteria ("roll back if error rate > X for Y min", not "if something goes wrong").
- Failure paths exist: what to do when a step fails, and how to undo it.

### 5. Format
- Heading hierarchy, lists, and tables consistent; tables where items have several attributes.
- Diagrams and images have captions and support a claim in the text.
- Only formatting that measurably hurts reading is a finding above NIT.

## Severity (shared scale)

| Tag | In a document this means |
|---|---|
| 🔴 **BLOCKER** | The reader will do the wrong thing, can't proceed, or is misled: a contradiction, a wrong fact, a non-executable step in a procedure, a missing rollback in a runbook |
| 🟠 **MAJOR** | The reader can proceed but will stumble or guess: undefined key term, missing edge case or decision criterion, missing section the type requires |
| 🟡 **MINOR** | Clarity or consistency issue that slows the reader: vague wording, inconsistent terms, weak structure |
| 💭 **NIT** | Polish; one line |

## Rules

1. **Location on every finding** — `Section > Subheading`, or `line N` for a file; `(document-wide)` only when it truly applies everywhere.
2. **Every finding has a fix** — the replacement text or the specific content to add. "Unclear" alone is not a finding.
3. **Merge one root cause into one finding** and list every location.
4. **No hedging on BLOCKERs** — say it blocks the reader and why.
5. **No invented facts** — in findings or in suggested fixes. When the fix needs a fact you don't have (the real threshold, the owner's name), write `[TODO: owner to supply …]` in the fix.
6. **One complete pass** — all findings at once.
7. **Specific praise only** — "What works" lists things to keep, not compliments.

## Verdict

Pick exactly one, applying the rules in order:
1. **Not ready** — any BLOCKER. Don't circulate until fixed.
2. **Needs revision** — any MAJOR.
3. **Ready** — MINOR/NIT only.

## Output format

`template.md` mirrors this format. A worked example is in `examples/example.txt` (if installed).

```markdown
# Document Review: [Document name]

**Type**: [PRD / design doc / runbook / guideline / README / …]
**Audience**: [stated, or "assumed: newcomer with no project context"]
**Findings**: 🔴 [n] · 🟠 [n] · 🟡 [n] · 💭 [n]
**Verdict**: [Not ready / Needs revision / Ready] — [one sentence]

## Summary
[1–3 sentences: the single biggest problem and what already works]

## Findings

### 🔴 BLOCKER
#### [B1] [Title]
**Location**: [Section > Subheading, or line N]
**Problem**: [what the reader would do wrong or be unable to do]
**Fix**: [replacement text or content to add]

### 🟠 MAJOR
[Same fields, IDs M1, M2…]

### 🟡 MINOR
[Same fields; Problem may be omitted when the Fix makes it obvious. IDs m1, m2…]

### 💭 NIT
- [Location] — [one line]

## Checked
- [Commands, paths, config keys, or links verified — and the result; external links listed as unverified]

## What works
- [Specific thing worth keeping]

## Top priorities
1. [Most important fix — IDs it closes]
```

Omit a severity section with no findings. Keep Top priorities to 3–5 items.

If a skill named here isn't installed, say which one fits, then help as far as this skill's own scope and rules allow.
