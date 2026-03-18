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
