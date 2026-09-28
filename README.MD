# Agent Skills Installer

Simple installer for AI coding agent skills.

Supports:

- Claude Code
- Windsurf

Installs a curated set of developer skills (code review, debugging, architecture, etc.) into the correct directories automatically.

---

## Quick Install

Install with one command:

```sh
curl -fsSL https://raw.githubusercontent.com/chicongst/agent-skills-installer/main/install.sh | bash
```

Install all skills:

```sh
curl -fsSL https://raw.githubusercontent.com/chicongst/agent-skills-installer/main/install.sh | bash -s -- --bundle all
```

Install for Windsurf:

```sh
curl -fsSL https://raw.githubusercontent.com/chicongst/agent-skills-installer/main/install.sh | bash -s -- --target windsurf
```

---

## Install Paths

| Target | Path |
|--------|------|
| Claude Code (global) | `~/.claude/skills` |
| Windsurf (global) | `~/.codeium/windsurf/skills` |
| Claude Code (workspace) | `./.claude/skills` |
| Windsurf (workspace) | `./.windsurf/skills` |

---

## Available Skills

| Skill | Description |
|-------|-------------|
| `architect` | System architecture, boundaries, data flow, consistency, failure modes, security & compliance, tradeoffs, rollout plans |
| `code-review` | Single-pass review of any code — bugs, edge cases, security/perf red flags, UI & accessibility, tests, verdict (C# goes to `dotnet-code-review` when installed) |
| `code-audit` | Full 20-dimension audit — architecture, SOLID, patterns, perf, security, DI, async, DB, API, domain — rule-based 0–10 scores, findings, action plan |
| `debug` | Reproducible failures — ranked hypotheses eliminated by experiment, proven root cause, minimal fix, regression test |
| `fix-bug` | Entry point for low-context bug reports — intake, investigation, reproduction, fix with explicit confidence (hands off to `debug` when several causes remain) |
| `refactor` | Simplify/restructure code without changing behavior — anti-patterns included |
| `test-writer` | Test plans and test code — expected values derived from code/spec, edge cases, dead-code findings, tests actually run |
| `security-review` | Trust boundaries, injection, authz/IDOR, SSRF, XXE, uploads, race conditions, tenant isolation, prompt injection, secrets, crypto — fixes plus regression tests |
| `docs-writer` | READMEs, tutorials, how-tos, runbooks, API references, ADRs — facts sourced from code, commands verified |
| `api-design` | Resources, status codes, Problem Details errors, pagination, idempotency, concurrency, versioning, webhooks |
| `algorithm-review` | Algorithm optimization, data structures, sorting/search improvements |
| `mastery` | Baseline senior engineering defaults when writing code — yields to task-specific skills and project conventions |
| `db-design` | Schema, keys, constraints, multi-tenant isolation, indexes derived from queries (rollout goes to `migration-safety`) |
| `migration-safety` | Safe migrations — lock behavior, `lock_timeout`, expand–contract, batched backfills, rollback, go/no-go |
| `sre-engineering` | Live incident response, SLIs/SLOs, error budgets, burn-rate alerting, blameless post-mortems |
| `release-readiness` | Release risk, rollout plan, tested rollback, monitoring, go/no-go |
| `performance-review` | Bottlenecks, profiling hotspots, measurement, optimization tradeoffs |
| `pr-review` | PR scope, risks, test gaps, change clarity, merge readiness |
| `changelog` | User-facing and developer-facing changelog entries from commits |
| `ui-design` | Design tokens, color palettes (light/dark), typography, spacing, UX, SEO |
| `document-review` | Strict document review — structure, clarity, consistency, accuracy checked against the repo, actionability; severity-tagged fixes and a verdict |
| `dotnet-code-review` | .NET / C# code review — blast radius, .NET slop scan, async/DI/EF Core/ASP.NET Core pitfalls, severity-tagged verdict |
| `dotnet-code-refactor` | Safe .NET / C# refactoring — code smells, risk classification, characterization tests, smallest-change-at-a-time (modifies code) |

---

## Skill Bundles

### `core`

- architect
- code-review
- code-audit
- debug
- fix-bug
- refactor
- test-writer
- security-review
- docs-writer
- api-design
- pr-review
- algorithm-review
- mastery

### `backend` = core +

- db-design
- migration-safety
- sre-engineering
- release-readiness
- performance-review

### `frontend` = core +

- ui-design
- performance-review

### `fullstack` = backend +

- changelog
- ui-design

### `dotnet` = core +

- dotnet-code-review
- dotnet-code-refactor

### `all` = fullstack + dotnet +

- document-review

---

## Usage

Basic install

```sh
./setup_agent_skills.sh
```

Install bundle

```sh
./setup_agent_skills.sh --bundle backend
```

Install to workspace

```sh
./setup_agent_skills.sh --scope workspace
```

Install for Windsurf

```sh
./setup_agent_skills.sh --target windsurf
```

Install, then verify every skill in the bundle (exits non-zero if any check fails)

```sh
./setup_agent_skills.sh --bundle all --verify
```

Update to the latest version (existing skills are skipped unless `--force` is given)

```sh
curl -fsSL https://raw.githubusercontent.com/chicongst/agent-skills-installer/main/install.sh | bash -s -- --bundle all --force
```

Remove skills this repo no longer ships (`incident-triage`, `ui-review`, `ux-copy`, `accessibility-review`, `planner`, `requirements-refiner`); without the flag the installer only warns

```sh
./setup_agent_skills.sh --bundle all --force --prune-retired
```

Uninstall a bundle

```sh
./setup_agent_skills.sh --uninstall --bundle core
```

Dry run, list bundles, self-test

```sh
./setup_agent_skills.sh --dry-run
./setup_agent_skills.sh --list
./setup_agent_skills.sh --self-test
```

`--without-support-files` installs only `SKILL.md` (no `template.md` or `examples/`).

---

## Using Skills

Claude Code

```
/architect
/code-review
/fix-bug
/debug
```

Windsurf

```
@architect
@code-review
@fix-bug
@debug
```

Skills may also be triggered automatically by context.

---

## Import Custom Skills

From GitHub

```sh
./setup_agent_skills.sh --import-github https://github.com/chicongst/agent-skills-installer
```

From local directory

```sh
./setup_agent_skills.sh --import-dir ./skills
```

Importing from the install root itself is skipped, so it never deletes your skills.

Skill structure

```
skill-name/
  SKILL.md            # required: frontmatter with name + description
  template.md         # optional: mirrors the output format in SKILL.md
  examples/example.txt  # optional: a worked example
```

---

## Contributing

PRs are welcome.

Each skill should follow the structure above. Keep the frontmatter valid YAML: quote the
`description` if it contains `: `, and make `name` match the folder name.
