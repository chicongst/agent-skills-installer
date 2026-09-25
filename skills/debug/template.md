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
