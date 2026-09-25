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
| `architect` | System architecture, boundaries, data flow, tradeoffs, rollout plans |
| `code-review` | Bugs, maintainability, correctness, edge cases, architecture issues |
| `code-audit` | Full 20-dimension audit — architecture, SOLID, patterns, perf, security, DI, async, DB, API, domain — scored with fixes |
| `debug` | Reproducible failures — ranked hypotheses eliminated by experiment, proven root cause, minimal fix, regression test |
| `fix-bug` | Entry point for low-context bug reports — intake, investigation, reproduction, fix with explicit confidence (hands off to `debug` when several causes remain) |
| `refactor` | Simplify/restructure code without changing behavior — anti-patterns included |
| `test-writer` | Test plans and test code — expected values derived from code/spec, edge cases, dead-code findings, tests actually run |
| `security-review` | Security risks, trust boundaries, secrets handling, abuse cases |
| `docs-writer` | Setup guides, ADRs, API references, usage instructions |
| `api-design` | Resources, contracts, error handling, versioning, examples |
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
| `document-review` | Strict document review — clarity, logic, consistency, accuracy, actionability, reader experience |
| `dotnet-code-review` | .NET / C# code review — blast radius, .NET slop scan, async/DI/EF Core/ASP.NET Core pitfalls, severity-tagged verdict |
| `dotnet-code-refactor` | Safe .NET / C# refactoring — code smells, risk classification, characterization tests, smallest-change-at-a-time (modifies code) |

---

## Skill Bundles

### `core`

- architect
- code-review
- debug
- fix-bug
- refactor
- test-writer
- security-review
- docs-writer
- api-design
- algorithm-review
- mastery

### `backend` = core +

- db-design
- migration-safety
- sre-engineering
- performance-review

### `frontend` = core +

- ui-design

### `fullstack` = backend +

- pr-review
- changelog
- ui-design

### `dotnet`

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

Verify installation

```sh
./setup_agent_skills.sh --verify
```

Dry run

```sh
./setup_agent_skills.sh --dry-run
```

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

Skill structure

```
skill-name/
  SKILL.md
```

---

## Contributing

PRs are welcome.

Each skill should follow

```
skill-name/
  SKILL.md
```
