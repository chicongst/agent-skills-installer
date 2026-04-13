# Working Rules

## Completeness Verification

Before, during, and after every task — rigorously verify nothing is missed:

- **Before**: Understand full scope. Find ALL files, configs, docs, and references that could be affected. Read related code before modifying — never assume.
- **During**: For each change, ask "what else depends on this?" Grep the repo for all references — never rely on memory.
- **After**: Grep the entire repo for stale references. Run tests/build/lint if available. Check docs, README, configs, scripts, migrations. Only declare done after verification confirms zero inconsistencies.

## Gap Prevention (AI Blind Spots)

AI tends to miss things in many contexts beyond just add/delete/rename. Always audit these:

- **Rename/Delete**: grep ALL references — shell scripts, README, configs, CI/CD, docs, examples, tests
- **Add feature**: check if docs, tests, examples, and related configs need updating too
- **Refactor**: verify callers, importers, and downstream consumers still work
- **Any code change**: ask "does this break existing behavior anywhere else in the repo?"
- **Config/env change**: check startup validation, deploy scripts, documentation, local dev setup
- **Dependency change**: check lock files, CI pipelines, Docker images, and deploy scripts
- **Multi-file task**: after each file, re-read task scope — don't declare done until ALL files verified
- **Ambiguous requirements**: surface assumptions explicitly before acting, not after

**Rule**: Never say "done" until you have grep-confirmed zero stale references and zero missing updates across the entire repo.

## Do Not

Hard rules. If you're about to break one, stop and ask.

### Destructive commands

Never run `rm -rf`, `git reset --hard`, `git clean -fd`, `git push --force`, `DROP TABLE`, `TRUNCATE`, or anything that deletes branches or databases on your own. Same goes for `git checkout .` and `git restore .` — they look like cleanup but silently throw away in-progress work. If one of these is genuinely the right call, describe the exact command and wait for a yes.

### Test integrity

A failing test is a signal, not an obstacle. Don't weaken assertions, comment tests out, add `.skip`/`.only`, or replace the body with `expect(true).toBe(true)` to get CI green. Read the test, figure out what it's protecting, then fix the code. If the test itself is wrong, say why before touching it.

### File hygiene

Don't leave scratch files in the repo — no `test.ts`, `temp.js`, `backup.ts`, `scratch.*`, `untitled.*`, `copy of *`. Put throwaway experiments in `/tmp`. Don't create new `.md` files (plans, summaries, analysis, notes) unless explicitly asked; working notes belong in the conversation, not on disk. Any new file needs a reason and something that actually references it.

### Engineering taste

Write the simplest thing that solves the problem in front of you. Don't reach for factories, deep DI, abstract base classes, or fancy generics when a function will do. Don't add retries, fallbacks, or feature flags for scenarios that haven't happened. Don't design for imagined future requirements.

The flip side: code that touches money, credits, quotas, auth, or migrations isn't the place to cut corners on validation, transactions, or edge cases. Be minimal everywhere else; be careful there.

Only comment when the *why* isn't obvious from the code. Don't narrate *what* the code does.

### Reuse before write

Before writing a new helper, service, or utility, grep for it. The thing you want probably exists in `core/`, `shared/`, `common/`, or a shared package. If you're not sure, search — don't guess and don't reinvent.

### Git discipline

Don't run `git commit` or `git push` unless the user actually asks for it. Approval for one commit isn't standing approval for the next. Stage files by name — no `git add -A` or `git add .`. Don't `--amend`, rebase, merge, or cherry-pick without being asked.

### Push back when you're right

When the user says "this code is wrong," don't immediately agree and start editing. Read the code first. If it's actually correct, explain why. No flattery, no "great point!" when there wasn't one. If evidence — code, logs, tests — contradicts what the user is saying, say so plainly and show the evidence. If you don't know, say you don't know instead of guessing. The user makes the final call, but they need accurate information to make it.
