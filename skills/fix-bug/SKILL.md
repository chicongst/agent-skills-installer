---
name: fix-bug
description: Use when the user reports a bug with little context — the entry point for bug reports such as an error message, a stack trace, "it's not working", "fix this", "why is this failing", "sửa lỗi này", "fix lỗi", "tại sao bị lỗi", "only one user has this", "restart fixed it", "chỉ máy tôi bị". Checks where the cause lives — code, config, data, client state (stale permissions, tokens, cache), or the user's environment — before diagnosing. Gathers scope, data flow, and history, asks only for what the code can't tell you, tries to reproduce, then applies a minimal fix with an explicit confidence level and a regression test. Not for a failure already reproducible that needs hypotheses eliminated — use `debug`; not for a live production incident — use `sre-engineering`.
---

# Fix Bug

Turn a thin bug report into a verified fix: gather context, reproduce, fix at the cause with a stated confidence — and hand off to `debug` when a hypothesis-elimination loop is needed.

## Rules

1. **Evidence before edits.** Every claim about the cause points to a `file:line`, a quoted log/error line, or a command's output. If it points to nothing, it is a hypothesis — label it as one.
2. **Don't ask what you can look up.** Read the stack trace, the code, the tests, and `git log` before asking the user anything. Ask only for what only they know.
3. **Root cause ≠ fix.** The root cause is a fact about the code, data, or environment; the fix is the change you make (see step 5). Never write a remedy in the root-cause field.
4. **Confidence gates the change** (see Confidence levels). Apply code only at High, or at Medium after the user confirms the open assumption.
5. **Minimal fix at the cause.** No retry around a race, no `try/catch` or null-check that hides a wrong value, no drive-by refactoring. If the fix changes behavior for other callers, call it out separately.
6. **No destructive or state-changing moves without asking** — no `git reset`, `git checkout .`, `git clean`, data deletion, or restarting shared services. Ask before `git stash` too — it hides the user's uncommitted work; a separate worktree (`git worktree add`) is the non-intrusive option. History inspection (`git log`, `git blame`, `git diff`) is read-only and fine.
7. **Follow the project's existing conventions** for code style, error handling, and test layout.
8. **Code is one suspect, not the default.** The cause can live in code, config, data, the client's state (permissions, tokens, caches, stored settings), or the user's environment (machine, OS, network). Don't name a code root cause until it also explains why *these* users or machines fail while others running the same code don't. A diagnosis that explains the error but not the scope is premature.
9. **Capture before reset.** Restarting, reinstalling, re-logging in, or clearing a cache often makes the failure disappear — and destroys the evidence of why. When the failure is still live, ask for the state first (logs, app/OS version, granted permissions, token claims, the affected record); then treat each reset as an experiment, one at a time.

## Fast path — obvious bugs

If the error pinpoints a line and the cause is visible there (typo in a name, wrong import path, missing argument, off-by-one next to the stack frame), don't run the full workflow. Fix it, state **Confidence: High — [one-line reason]**, run the failing command or nearest test to confirm, add a regression test unless that command already is a test or build/type check that would catch a recurrence, and use the short output at the end. If the "obvious" fix doesn't make the failure go away, drop back to step 1. The fast path never applies when the failure hits only some users or machines on the same code — that scope is the first thing to explain.

## Workflow

### 1. Intake — extract, look, then ask

From what the user gave, extract: exact error text, `file:line` frames, the command/action that triggered it, environment, and expected vs actual behavior. Then check what's still missing:

| Needed | Why it matters |
|---|---|
| Expected vs actual, concretely | Without it you can't tell the bug from intended behavior |
| Exact trigger (input, request, steps, test name) | Needed to reproduce |
| Frequency: always / sometimes / once | "Sometimes" points at timing, state, or data variation |
| Environment where it fails vs where it works | The difference is often the cause |
| Did it ever work? What changed since (deploy, dependency, config, data)? | Narrows the search to a diff |
| Full stack trace / logs, not a screenshot crop | The first error and "caused by" chain usually matter most |
| Who is affected: one user/device/account, a group, or everyone? Does the same action work with another account, another device, or a fresh install/login? | Same code, different outcome → the cause is in what differs (state, environment, data), not in the shared code path |
| What has the user already tried (restart, re-login, reinstall, clear cache, other browser) and what happened? | A failure that a reset cures lived in the state that reset cleared — that is a lead, not a closed case |

Before asking, take a first look — open the files in the stack trace, find the relevant tests, run `git log --oneline -15 -- <file>` — and fill in anything the code or history answers (Rule 2). Ask for the rest in **one batch** of at most four questions, most important first — use AskUserQuestion if available, otherwise ask in plain text with short suggested answers (e.g. "Which environment? local / staging / production / all"). If the user can't answer, continue with the assumption stated explicitly.

### 2. Investigate — scope, data flow, history

- **Place the cause before tracing code.** From the intake, decide where the difference between failing and working cases can live, and check the cheapest location first:

| Location | Typical causes | How to check |
|---|---|---|
| Client state | Permissions or consent granted by an older version — OAuth scopes, OS runtime permissions (camera, notifications, location, files), browser permissions, roles/grants — when the current version needs more; tokens or sessions issued with old claims; local cache, storage, or service worker from an older build; stored settings in an old format | Compare what the failing user actually holds (granted scopes/permissions, decoded token claims, app version, cached data) with what the current code requires; compare with a new user or fresh install |
| Environment | OS or browser version, low disk or memory, clock skew, proxy/VPN/firewall/antivirus, locale or time zone, long-running process that leaked or stuck | Versions and resources from logs or the user; the same action on another machine or network |
| Data | One record, tenant, or account in a state the code didn't expect | Query the affected record; try the action on another record |
| Config / flags | Per-user or per-tenant feature flags, environment config, a secret that rotated | Flag and config values for the failing vs a working user |
| Code | Logic, contracts, concurrency — the rest of this workflow | Trace below |

- **Locate the failure point.** Open the top in-project stack frame (skip library frames). With no stack trace, grep for the error message text or the UI string/endpoint involved.
- **Trace the data backward** from the failure point to its source: which function produced the bad value, what input it received, what transformations sit in between (parsing, mapping, serialization, caching). The bug lives where expected and actual first diverge.
- **Map what the path depends on**: shared state (globals, caches, singletons, session), config and env vars, external calls (DB, APIs, queues), and concurrency (async boundaries, threads, parallel requests).
- **Check history** when it "used to work": `git log --oneline -15 -- <file>`, `git log -L <start>,<end>:<file>` for a function's history, `git blame -L <start>,<end> <file>`, and a lockfile diff for dependency bumps.
- **Match the symptom to common causes** to decide where to look first:

| Symptom | Look first at |
|---|---|
| null/undefined/`NoneType` error | Optional data (missing field, empty result, unset config) reaching code that assumes presence |
| Wrong value, no error | Transform/mapping steps, units, time zones, default values, stale cache |
| Works locally, fails elsewhere | Config/env vars, dependency versions, data volume, file paths, permissions |
| Intermittent | Unawaited async, shared mutable state, ordering assumptions, timeouts, test pollution |
| Started after a deploy/upgrade | The diff between last-good and current, including lockfiles and config |
| Only some users/devices, same code and version | Their state or environment (table above): permissions, tokens, cache, OS, network, data |
| Existing users fail after an app upgrade, new installs/accounts work | State created by the old version: permissions or scopes granted before the new one was required, persisted settings or cache in the old format, sessions with old claims |
| Cured by restart / re-login / reinstall / clearing cache | Whatever that reset rebuilt: in-memory state, a stuck lock or leaked resource, token claims, local storage, a permission re-prompt — then ask why the code let that state break it |
| 4xx/5xx from an integration | Contract mismatch: field names, types, auth, serialization |

### 3. Reproduce

When only some clients fail, reproduce their *state*, not just their input: an account created on the old version, a token issued with the old scopes, permission Y denied, the cache from the previous build. Turn the trigger into something runnable: a failing test (preferred — it becomes the regression test), a script, a `curl`, or exact manual steps. Run it and confirm the failure matches the reported symptom. If you can't run it, give the user the exact command and ask for the output.

If it won't reproduce, say so, list what differs between your attempt and the report, and ask for the missing piece (data sample, env, logs at a finer level) rather than fixing blind.

### 4. Decide: fix or hand off

- **One cause explains every observation** (including odd ones: why only in prod, why only sometimes, why only these users or machines) → go to step 5.
- **Reproducible, but two or more plausible causes remain** → follow the `debug` skill's loop (hypothesize → one-variable experiments → prove the root cause) starting from your reproduction. Carry over your intake and investigation findings as its Symptom and Reproduction; debug's report then replaces this skill's output. If `debug` isn't installed: list each hypothesis with the observation that would distinguish it, run the cheapest distinguishing check first, and don't fix until one remains.
- **Not reproducible, causes still open** → don't change code. Report at Low confidence with the hypotheses and the specific data that would separate them (a log line to add, a query to run, a config to compare).

### 5. Fix

- State the root cause as a causal chain with `file:line`: cause → intermediate effect → observed symptom. If you use "why?" chains, stop at the first cause you can change and state it as a fact; e.g. *slow endpoint → full scan on `orders` → no index on `orders.customer_id`* is the root cause; *add the index* is the fix.
- **When the trigger is client state or environment, report two things.** The *workaround* for affected users (re-login, re-grant the permission, restart, clear the cache) — it is not the fix. And the *code gap* that let that state break the app: it never checks granted permissions or scopes against what it now needs, doesn't re-request consent after an upgrade, doesn't invalidate an old cache, or fails with a generic error instead of telling the user what to do. The root cause names both ("users who consented before v2.3 lack scope Y → the upload call gets 403 → the app shows a blank screen because it never checks granted scopes"). If the environment alone explains it with no code gap (disk full), say so and change no code.
- Make the smallest change that removes that cause. Check callers of anything you change (grep) and note any behavior change for them.
- Grep for the same pattern elsewhere; list the hits rather than silently fixing them all.

### 6. Regression test and verification

- Add a test that reproduces the bug. It must fail on the old code and pass on the new. If you wrote it in step 3 and saw it fail before the fix, that is the "before" run. Otherwise temporarily undo only your own fix edit (you know the exact lines), run the test, and re-apply the edit — don't use `git stash` or `git checkout` for this, since they also move the user's uncommitted changes in the same files.
- Rerun the original reproduction; run the surrounding test suite (and lint/type-check if the project has them).

## Confidence levels

| Level | Meaning | Allowed action |
|---|---|---|
| **High** | Reproduced, cause traced to `file:line`, fix verified against the reproduction (or a fast-path fix confirmed by rerunning) | Apply the fix |
| **Medium** | Cause traced in code but not reproduced, or one stated assumption unverified | Propose the fix; apply after the user confirms the assumption |
| **Low** | Key information missing; cause is a hypothesis | No code change — give hypotheses and the next data to collect |

Every Medium or Low report ends with the specific questions or checks that would raise it.

## Output format

```markdown
## Bug: [one-line title]
**Confidence**: High / Medium / Low — [why, in one line]
**Cause location**: [code / config / data / client state / environment] — [why only these users/machines, or "all users"]

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
**Workaround for affected users**: [re-login / re-grant / restart / … — or "none needed"]
**Behavior change for other callers**: [none / what changes]
**Same pattern elsewhere**: [grep command + hits, or "none found"]

### Verification
- [ ] Regression test `[name]` fails before, passes after — [command + result]
- [ ] Original reproduction passes — [result]
- [ ] Surrounding suite passes — [command + result]

### Open questions (Medium/Low only)
- [question or check that would raise confidence]
```

For the fast path, use only the title, Confidence, Root cause, Fix, and a one-line Verification. Omit sections that don't apply rather than filling them with "N/A". `template.md` mirrors this format. A worked example is in `examples/example.txt` (if installed).

If a skill named here isn't installed, say which one fits, then help as far as this skill's own scope and rules allow.
