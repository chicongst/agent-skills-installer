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

Claude Code

~/.claude/skills

Windsurf

~/.codeium/windsurf/skills

Workspace install

./.claude/skills
./.windsurf/skills

---

## Skill Bundles

core

- architect
- code-review
- debug
- refactor
- test-writer
- security-review
- docs-writer
- api-design
- algorithm-review
- mastery

backend = core +

- db-design
- migration-safety
- sre-engineering
- performance-review

frontend = core +

- ui-design

fullstack = backend +

- pr-review
- changelog
- ui-design

all = fullstack (all skills)

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

/architect
/code-review
/debug

Windsurf

@architect
@code-review
@debug

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

skill-name/
  SKILL.md

---

## Contributing

PRs are welcome.

Each skill should follow

skill-name/
  SKILL.md
