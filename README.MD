# Agent Skills Installer

Simple installer for AI coding agent skills.

Supports:

- Claude Code
- Windsurf

Installs a curated set of developer skills (planner, code review, debugging, architecture, etc.) into the correct directories automatically.

---

## Quick Install

Install with one command:

curl -fsSL https://raw.githubusercontent.com/YOURNAME/agent-skills-installer/main/install.sh | bash

Install all skills:

curl -fsSL https://raw.githubusercontent.com/YOURNAME/agent-skills-installer/main/install.sh | bash -s -- --bundle all

Install for Windsurf:

curl -fsSL https://raw.githubusercontent.com/YOURNAME/agent-skills-installer/main/install.sh | bash -s -- --target windsurf

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

- planner
- architect
- code-review
- debug
- refactor
- test-writer
- security-review
- docs-writer
- api-design
- release-readiness

backend

- db-design
- migration-safety
- incident-triage
- performance-review

frontend

- ui-review
- accessibility-review
- ux-copy

fullstack

- requirements-refiner
- pr-review
- changelog

---

## Usage

Basic install

./setup_agent_skills.sh

Install bundle

./setup_agent_skills.sh --bundle backend

Install to workspace

./setup_agent_skills.sh --scope workspace

Install for Windsurf

./setup_agent_skills.sh --target windsurf

Verify installation

./setup_agent_skills.sh --verify

Dry run

./setup_agent_skills.sh --dry-run

---

## Using Skills

Claude Code

/planner  
/code-review  
/debug  

Windsurf

@planner  
@code-review  
@debug  

Skills may also be triggered automatically by context.

---

## Import Custom Skills

From GitHub

./setup_agent_skills.sh --import-github https://github.com/chicongst/agent-skills-installer

From local directory

./setup_agent_skills.sh --import-dir ./skills

Skill structure

skill-name/
  SKILL.md

---

## Contributing

PRs are welcome.

Each skill should follow

skill-name/
  SKILL.md
