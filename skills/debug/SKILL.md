---
name: debug
description: Use when a failure is already observable or reproducible (failing test, erroring command, triggerable wrong output, flaky failure you can loop) and you need the proven root cause — rank hypotheses, eliminate them with one-variable experiments, fix only what the evidence confirms. Triggers: "debug this", "find the root cause", "fails only in CI", "flaky test", "tìm root cause". Not for a low-context bug report (just an error or "it's not working") — use `fix-bug`; not for a live production incident — use `sre-engineering`; not for slowness alone — use `performance-review`.
---

# Debug

Find the root cause of an observable failure by eliminating hypotheses with experiments, then fix it and prove the fix. Every conclusion in the report must point to an experiment result or a quoted line of output — not to intuition.

## Entry check

Before starting, confirm you have (or can build) all three:

1. **A symptom stated as expected vs actual** — exact error text, wrong value, or exit code. Paraphrase is not enough.
2. **A trigger** — a command, test, input, or sequence that produces the failure, plus how often (e.g. "every run", "3 of 20 runs").
3. **Access** — you can run it, or the user can run commands you give and paste the output.

If something is missing, ask for it (use AskUserQuestion if available, otherwise ask in plain text) — batch the questions, don't drip them.

## Rules

1. **Reproduce first** (step 2) — a failure you cannot trigger is a failure you cannot prove fixed.
2. **Write the prediction before running the experiment.** "If H2 is true, running the test alone will pass." An experiment without a prediction proves nothing.
3. **Change one variable per experiment.** Two changes in one run make the result uninterpretable.
4. **Record the evidence verbatim.** Command run + the relevant output lines. Mark a line as trimmed rather than paraphrasing it.
5. **Eliminate, don't just confirm.** Confirmed means toggling that one cause turns the failure off and back on, with competitors eliminated.
6. **Read the whole error.** Full stack trace, every "caused by", the first error in the log rather than the last.
7. **Question "can't happen" assumptions** by checking them (print, assert, breakpoint) instead of reasoning about them.
8. **Ask before any destructive or state-changing move** — `git reset`, `git checkout .`, `git clean`, `git bisect`, switching branches, dropping data, restarting shared services. Protect uncommitted work with `git stash` or a separate worktree.

## Workflow

### 1. Pin the symptom
Quote the exact failure. Note what changed recently (deploy, dependency, config, data, traffic) and what still works — a working neighbour is the best comparison baseline.

### 2. Reproduce and minimize
- Turn the trigger into a single command and rerun it to confirm the failure repeats. If it fails in only one environment, that difference is your first lead.
- **Intermittent failures**: loop it and count failures (`for i in $(seq 50); do <cmd> >/dev/null 2>&1 || echo FAIL; done | grep -c FAIL`) to get the rate. Silence the command's own output so its text can't inflate the count. A rate is your baseline for judging experiments; "0 failures in N runs" only bounds the failure rate below roughly 3/N at 95% confidence (rule of three), so pick N accordingly.
- Shrink the case: remove inputs, tests, config, and code paths that are not needed for the failure. Stop when removing anything else makes it pass.

### 3. Hypothesize
List 3–5 candidate causes. For each, write the observable **prediction** that would distinguish it from the others. Order by likelihood × cheapness of the experiment — a 30-second experiment on a medium-likelihood cause often beats a one-hour experiment on the favourite.

### 4. Experiment
Pick the technique that separates the remaining hypotheses fastest:

| Technique | Use when |
|---|---|
| Isolation vs combination (run alone / with others / reordered) | Passes alone, fails in a suite; test pollution; shared state |
| Environment diff (run the failing environment's exact command locally, or vice versa) | "Works on my machine", CI-only, one host only |
| Bisect history (`git bisect`, Rule 8) | It used to work and a known-good commit exists |
| Bisect input (halve the data/config until the minimal trigger remains) | Fails on large or specific inputs |
| Instrument at a boundary (log/assert/print the value entering and leaving a step) | Wrong value appears somewhere in a pipeline |
| Debugger / breakpoint on the failing line | Need live state at the moment of failure |
| Force the timing (sleeps, barriers, single-threaded mode, fixed seed) | Race, ordering, or randomness suspected |
| Swap one dependency (pin version, stub the external call) | Library, network, or third-party behavior suspected |

After each experiment, update the hypothesis table: **Eliminated**, **Confirmed**, or **Open**. If every hypothesis is eliminated, your model of the system is wrong — go back to step 1 and re-check the assumptions you did not test.

### 5. State the root cause
Write the causal chain from cause to symptom, with `file:line`. Explain every observation, including the odd ones (why only in CI, why only 1 in N, why the error message says what it says). If an observation is unexplained, the investigation is not done.

### 6. Fix at the cause
- Smallest change that removes the cause, not the symptom (no retry around a race, no `try/except` around a wrong value).
- Check whether the current behavior is relied on elsewhere before changing it; if the fix changes behavior for other callers, call that out separately.
- Follow the project's existing conventions for code and tests.

### 7. Verify and prevent
- Rerun the original reproduction: it now passes (for intermittent failures, run the same loop count as the baseline).
- Add a regression test that fails on the old code and passes on the new one — run it against both.
- Run the surrounding test suite.
- Search for the same pattern elsewhere (grep, linter rule) and list the hits.

## When stuck or out of budget

Stop and report instead of guessing. Deliver the report with the root cause marked **Not yet proven**, the hypothesis table as it stands, and the specific data or access needed to continue (a log at a given level, a heap dump, production config, a failing input). Suggest the next experiment, not a speculative fix.

## Output Format

```markdown
# Debug Report: [Issue title]

## Symptom
- **Expected**: [what should happen]
- **Actual**: [exact error / wrong value, quoted]
- **Frequency**: [every run / N of M runs / only under condition X]
- **Environment**: [where it fails and where it does not]

## Reproduction
[Single command or minimal steps, plus the output that shows the failure]

## Hypotheses and Experiments
| # | Hypothesis | Prediction if true | Experiment | Result | Status |
|---|---|---|---|---|---|
| H1 | [candidate cause] | [what we would observe] | [command / action] | [observed output] | Eliminated / Confirmed / Open |

## Root Cause
**Cause**: [one sentence]
**Where**: [file:line]
**Causal chain**: [cause → intermediate effect → observed symptom; explains every observation]
**Confidence**: [Proven (toggled off and on; competitors eliminated) / Not yet proven — what is missing]

## Fix
[Minimal diff or code]
**Why it works**: [link from fix to cause]
**Risk / behavior change**: [who else is affected; anything that changes for other callers]

## Verification
- [ ] Original reproduction passes — [command + result]
- [ ] Regression test fails on old code, passes on new — [test name]
- [ ] Surrounding suite passes — [command + result]
- [ ] Same pattern searched — [command + hits]
```

Keep the Hypotheses table to the hypotheses you actually considered; drop none silently — an eliminated hypothesis with its evidence is part of the proof. `template.md` mirrors this format. A worked example is in `examples/example.txt` (if installed).
