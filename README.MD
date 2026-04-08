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
| `debug` | Failures — symptoms, root cause, validation steps, concrete fixes |
| `fix-bug` | Deep bug investigation — gathers context, traces root cause, proposes verified fix |
| `refactor` | Simplify/restructure code without changing behavior — anti-patterns included |
| `test-writer` | Critical flows, edge cases, regression risks |
| `security-review` | Security risks, trust boundaries, secrets handling, abuse cases |
| `docs-writer` | Setup guides, ADRs, API references, usage instructions |
| `api-design` | Resources, contracts, error handling, versioning, examples |
| `algorithm-review` | Algorithm optimization, data structures, sorting/search improvements |
| `mastery` | Senior-level engineering principles applied automatically to any code |
| `db-design` | Schema, indexing, constraints, query patterns, migration strategy |
| `migration-safety` | Safe migrations — rollback, backward compatibility, observability |
| `sre-engineering` | Production incidents, reliability, on-call triage, post-mortems |
| `performance-review` | Bottlenecks, profiling hotspots, measurement, optimization tradeoffs |
| `pr-review` | PR scope, risks, test gaps, change clarity, merge readiness |
| `changelog` | User-facing and developer-facing changelog entries from commits |
| `ui-design` | Design tokens, color palettes (light/dark), typography, spacing, UX, SEO |

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

### `all` = fullstack (all skills)

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
