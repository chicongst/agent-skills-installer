#!/usr/bin/env bash
set -euo pipefail

TARGET="claude"
SCOPE="global"
BUNDLE="core"
FORCE=0
VERIFY=0
DRY_RUN=0
UNINSTALL=0
SELF_TEST=0
WITHOUT_SUPPORT_FILES=0
IMPORT_GITHUB=""
IMPORT_DIR=""
LIST_ONLY=0

SCRIPT_NAME="$(basename "$0")"

usage() {
  cat <<'EOF'
Usage:
  ./setup_agent_skills.sh [options]

Options:
  --target <claude|windsurf>                      Default: claude
  --scope <global|workspace>                      Default: global
  --bundle <core|backend|frontend|fullstack|all> Default: core
  --import-github <url>                           Import skill folders from a GitHub repo
  --import-dir <path>                             Import skill folders from a local directory
  --without-support-files                         Do not create support files
  --verify                                        Verify installed skills
  --dry-run                                       Print actions only
  --force                                         Overwrite existing skills
  --uninstall                                     Remove installed/generated skills for selected bundle
  --self-test                                     Validate generated skill structure in temp dir
  --list                                          List bundles, skills, paths, and usage
  -h, --help                                      Show help

Examples:
  ./setup_agent_skills.sh
  ./setup_agent_skills.sh --bundle all --verify
  ./setup_agent_skills.sh --target windsurf --scope workspace --bundle backend
  ./setup_agent_skills.sh --import-github https://github.com/owner/repo
  ./setup_agent_skills.sh --import-dir ./skills --force
  ./setup_agent_skills.sh --dry-run --bundle all
  ./setup_agent_skills.sh --uninstall --bundle core
EOF
}

log() { printf '%s\n' "$*"; }
err() { printf 'Error: %s\n' "$*" >&2; exit 1; }

need_cmd() {
  command -v "$1" >/dev/null 2>&1 || err "Missing required command: $1"
}

run_cmd() {
  if [[ "$DRY_RUN" -eq 1 ]]; then
    printf '[dry-run] '
    printf '%q ' "$@"
    printf '\n'
  else
    "$@"
  fi
}

target_root() {
  case "$TARGET:$SCOPE" in
    claude:global)      echo "$HOME/.claude/skills" ;;
    claude:workspace)   echo "$(pwd)/.claude/skills" ;;
    windsurf:global)    echo "$HOME/.codeium/windsurf/skills" ;;
    windsurf:workspace) echo "$(pwd)/.windsurf/skills" ;;
    *) err "Unsupported target/scope: $TARGET / $SCOPE" ;;
  esac
}

manual_prefix() {
  case "$TARGET" in
    claude) echo "/" ;;
    windsurf) echo "@" ;;
    *) echo "" ;;
  esac
}

skills_for_bundle() {
  case "$1" in
    core)
      cat <<'EOF'
planner
architect
code-review
debug
refactor
test-writer
security-review
docs-writer
api-design
release-readiness
EOF
      ;;
    backend)
      cat <<'EOF'
planner
architect
code-review
debug
refactor
test-writer
security-review
docs-writer
api-design
release-readiness
db-design
migration-safety
incident-triage
performance-review
EOF
      ;;
    frontend)
      cat <<'EOF'
planner
architect
code-review
debug
refactor
test-writer
security-review
docs-writer
api-design
release-readiness
ui-review
accessibility-review
ux-copy
EOF
      ;;
    fullstack)
      cat <<'EOF'
planner
architect
code-review
debug
refactor
test-writer
security-review
docs-writer
api-design
release-readiness
db-design
migration-safety
incident-triage
performance-review
ui-review
accessibility-review
ux-copy
requirements-refiner
pr-review
changelog
EOF
      ;;
    all)
      cat <<'EOF'
planner
architect
code-review
debug
refactor
test-writer
security-review
docs-writer
api-design
release-readiness
db-design
migration-safety
incident-triage
performance-review
ui-review
accessibility-review
ux-copy
requirements-refiner
pr-review
changelog
EOF
      ;;
    *)
      err "Unknown bundle: $1"
      ;;
  esac
}

skill_description() {
  case "$1" in
    planner) echo "Break down complex tasks into ordered steps, dependencies, risks, and execution plans." ;;
    architect) echo "Design system architecture, boundaries, data flow, tradeoffs, and rollout plans." ;;
    code-review) echo "Review code for bugs, maintainability, correctness, edge cases, and architecture issues." ;;
    debug) echo "Debug failures by identifying symptoms, root causes, validation steps, and concrete fixes." ;;
    refactor) echo "Refactor code for readability, modularity, performance, and maintainability without changing behavior." ;;
    test-writer) echo "Design and write focused tests covering critical flows, edge cases, and regression risks." ;;
    security-review) echo "Review for common security risks, trust boundaries, secrets handling, and abuse cases." ;;
    docs-writer) echo "Write concise technical documentation, setup guides, ADRs, and usage instructions." ;;
    api-design) echo "Design APIs with resources, contracts, error handling, versioning, and examples." ;;
    release-readiness) echo "Assess release readiness including checks, rollback plans, monitoring, and communication." ;;
    db-design) echo "Design database schema, indexing, integrity constraints, query patterns, and migration strategy." ;;
    migration-safety) echo "Plan and review data or schema migrations for safety, rollback, compatibility, and observability." ;;
    incident-triage) echo "Triage production incidents with timeline, hypotheses, mitigations, ownership, and follow-up." ;;
    performance-review) echo "Review performance bottlenecks, measurement strategy, hotspots, and optimization tradeoffs." ;;
    ui-review) echo "Review UI quality for clarity, consistency, states, error handling, and interaction details." ;;
    accessibility-review) echo "Review accessibility concerns across semantics, keyboard flow, contrast, and assistive tech support." ;;
    ux-copy) echo "Write and improve UX copy for clarity, tone, empty states, errors, and calls to action." ;;
    requirements-refiner) echo "Refine ambiguous requirements into constraints, acceptance criteria, risks, and open questions." ;;
    pr-review) echo "Review pull requests for scope, risks, test gaps, change clarity, and merge readiness." ;;
    changelog) echo "Produce user-facing and developer-facing changelog entries from commits or merged changes." ;;
    *) echo "General-purpose engineering skill." ;;
  esac
}

skill_body() {
  case "$1" in
    planner) cat <<'EOF'
You are a project planner.

When invoked:
1. Restate the objective in one paragraph.
2. Produce a high-level plan.
3. Break work into concrete subtasks.
4. Call out dependencies, blockers, and assumptions.
5. Identify risks and mitigations.
6. Suggest execution order and checkpoints.

Output sections:
- Objective
- Plan
- Subtasks
- Dependencies
- Risks
- Checkpoints
EOF
      ;;
    architect) cat <<'EOF'
You are a principal software architect.

When invoked:
1. Clarify the problem and non-goals.
2. Propose the architecture and major components.
3. Explain data flow and integration points.
4. Discuss tradeoffs, scaling concerns, and failure modes.
5. Recommend rollout and observability.

Output sections:
- Problem
- Architecture
- Components
- Data Flow
- Tradeoffs
- Rollout
EOF
      ;;
    code-review) cat <<'EOF'
You are a senior reviewer.

Review for:
- Correctness
- Bugs and edge cases
- Maintainability
- Complexity
- Test coverage gaps
- Security and performance concerns

Output sections:
- Summary
- Findings
- Severity
- Suggested Changes
- Safer/Better Version
EOF
      ;;
    debug) cat <<'EOF'
You are a debugging specialist.

When invoked:
1. Identify the observed symptoms.
2. Form likely root-cause hypotheses.
3. Rank hypotheses by probability.
4. Suggest quick validation steps.
5. Provide the fix and how to confirm it.

Output sections:
- Symptoms
- Hypotheses
- Validation
- Root Cause
- Fix
- Verification
EOF
      ;;
    refactor) cat <<'EOF'
You are a refactoring specialist.

Goals:
- Improve readability
- Improve modularity
- Reduce duplication
- Preserve behavior
- Improve naming and cohesion

Output sections:
- Current Issues
- Refactor Plan
- Improved Code
- Behavioral Guarantees
EOF
      ;;
    test-writer) cat <<'EOF'
You are a test engineering specialist.

When invoked:
1. Identify critical paths and edge cases.
2. Propose a test strategy.
3. Write focused tests.
4. Explain what each test protects against.

Output sections:
- Test Strategy
- Cases
- Test Code
- Remaining Gaps
EOF
      ;;
    security-review) cat <<'EOF'
You are an application security reviewer.

Review for:
- Input validation
- Authn/Authz issues
- Secrets exposure
- Injection risks
- SSRF/XSS/CSRF where relevant
- Unsafe deserialization
- Logging/privacy leaks
- Dependency and supply-chain concerns

Output sections:
- Threat Surface
- Findings
- Severity
- Recommended Fixes
- Hardening Checklist
EOF
      ;;
    docs-writer) cat <<'EOF'
You are a technical writer.

When invoked:
1. Identify the audience.
2. Write concise, accurate instructions.
3. Include prerequisites and examples.
4. End with troubleshooting or FAQ when useful.

Output sections:
- Audience
- Prerequisites
- Steps
- Examples
- Troubleshooting
EOF
      ;;
    api-design) cat <<'EOF'
You are an API designer.

When invoked:
1. Define resources and responsibilities.
2. Propose endpoints and payload shapes.
3. Specify validation and error handling.
4. Address pagination, idempotency, and versioning where applicable.
5. Include examples.

Output sections:
- Goals
- Resources
- Endpoints
- Schemas
- Errors
- Examples
EOF
      ;;
    release-readiness) cat <<'EOF'
You are a release manager.

When invoked:
1. Evaluate scope and risk.
2. Confirm testing and migration readiness.
3. Define rollout, rollback, and monitoring.
4. Prepare communication and ownership.

Output sections:
- Scope
- Risk
- Checklist
- Rollout
- Rollback
- Monitoring
- Communication
EOF
      ;;
    db-design) cat <<'EOF'
You are a database design specialist.

When invoked:
1. Model core entities and relationships.
2. Propose schema and constraints.
3. Suggest indexes based on query patterns.
4. Address migration and backfill strategy.

Output sections:
- Entities
- Schema
- Indexing
- Query Patterns
- Migration Plan
EOF
      ;;
    migration-safety) cat <<'EOF'
You are a migration safety reviewer.

When invoked:
1. Identify compatibility constraints.
2. Evaluate expand-migrate-contract path.
3. Define rollback strategy.
4. Call out data-loss or downtime risk.
5. Recommend metrics and validation.

Output sections:
- Change Summary
- Risks
- Safe Sequence
- Rollback
- Validation
EOF
      ;;
    incident-triage) cat <<'EOF'
You are an incident commander assistant.

When invoked:
1. Summarize impact and blast radius.
2. Build a hypothesis list.
3. Propose immediate mitigations.
4. Assign owners and next checks.
5. Capture a draft incident timeline.

Output sections:
- Impact
- Hypotheses
- Mitigations
- Owners
- Timeline
- Follow-up
EOF
      ;;
    performance-review) cat <<'EOF'
You are a performance review specialist.

When invoked:
1. Identify the user-visible bottleneck.
2. Ask for or infer measurements.
3. Locate likely hotspots.
4. Recommend low-risk improvements first.
5. Explain tradeoffs.

Output sections:
- Bottleneck
- Evidence
- Hotspots
- Improvements
- Tradeoffs
EOF
      ;;
    ui-review) cat <<'EOF'
You are a UI reviewer.

Review for:
- Visual hierarchy
- Consistency
- States and transitions
- Error handling
- Empty/loading states
- Accessibility basics

Output sections:
- Summary
- Findings
- Suggested Improvements
EOF
      ;;
    accessibility-review) cat <<'EOF'
You are an accessibility reviewer.

Review for:
- Semantic structure
- Keyboard access
- Focus order
- Labels and names
- Contrast
- Screen reader compatibility

Output sections:
- Findings
- Severity
- Fixes
- Quick Wins
EOF
      ;;
    ux-copy) cat <<'EOF'
You are a UX copywriter.

When invoked:
1. Identify user intent and moment.
2. Rewrite copy for clarity and confidence.
3. Keep it concise and actionable.
4. Offer 2-3 tone variants when helpful.

Output sections:
- Current Problem
- Revised Copy
- Alternatives
EOF
      ;;
    requirements-refiner) cat <<'EOF'
You are a product requirements refiner.

When invoked:
1. Turn vague requests into a crisp problem statement.
2. Identify constraints and assumptions.
3. Draft acceptance criteria.
4. Surface open questions and risks.

Output sections:
- Problem Statement
- Constraints
- Acceptance Criteria
- Open Questions
- Risks
EOF
      ;;
    pr-review) cat <<'EOF'
You are a pull request reviewer.

When invoked:
1. Summarize what changed.
2. Identify risky areas.
3. Check clarity, tests, and migration impact.
4. Recommend merge blockers vs nits.

Output sections:
- Summary
- Blockers
- Risks
- Nits
- Merge Readiness
EOF
      ;;
    changelog) cat <<'EOF'
You are a changelog writer.

When invoked:
1. Group changes by user impact.
2. Write concise entries.
3. Separate user-facing notes from internal notes.
4. Call out migrations, deprecations, and breaking changes.

Output sections:
- User-Facing
- Developer Notes
- Breaking Changes
- Upgrade Notes
EOF
      ;;
    *) cat <<'EOF'
You are a specialized engineering assistant.

Output sections:
- Summary
- Findings
- Recommendations
EOF
      ;;
  esac
}

support_template() {
  local skill="$1"
  case "$skill" in
    planner) cat <<'EOF'
# Planning Template

## Objective
## Assumptions
## Milestones
## Risks
## Checkpoints
EOF
      ;;
    architect) cat <<'EOF'
# Architecture Template

## Context
## Components
## Data Flow
## Tradeoffs
## Rollout
EOF
      ;;
    code-review) cat <<'EOF'
# Review Template

## Summary
## Findings
## Severity
## Fixes
EOF
      ;;
    debug) cat <<'EOF'
# Debug Template

## Symptoms
## Hypotheses
## Validation
## Root Cause
## Fix
EOF
      ;;
    *) cat <<'EOF'
# Template

## Summary
## Details
## Output
EOF
      ;;
  esac
}

skill_dir_exists() {
  local dir="$1"
  [[ -d "$dir" ]]
}

write_skill() {
  local root="$1"
  local skill="$2"
  local dir="$root/$skill"
  local desc body

  desc="$(skill_description "$skill")"
  body="$(skill_body "$skill")"

  if skill_dir_exists "$dir" && [[ "$FORCE" -ne 1 ]]; then
    log "skip   $dir (exists, use --force to overwrite)"
    return 0
  fi

  run_cmd mkdir -p "$dir"

  if [[ "$DRY_RUN" -eq 1 ]]; then
    log "[dry-run] write $dir/SKILL.md"
  else
    cat > "$dir/SKILL.md" <<EOF
---
name: $skill
description: $desc
---

$body
EOF
  fi

  if [[ "$WITHOUT_SUPPORT_FILES" -ne 1 ]]; then
    if [[ "$DRY_RUN" -eq 1 ]]; then
      log "[dry-run] write $dir/template.md"
      log "[dry-run] mkdir -p $dir/examples"
      log "[dry-run] write $dir/examples/example.txt"
    else
      cat > "$dir/template.md" <<EOF
$(support_template "$skill")
EOF
      mkdir -p "$dir/examples"
      cat > "$dir/examples/example.txt" <<EOF
Example usage for skill: $skill
EOF
    fi
  fi

  log "install $skill"
}

remove_skill() {
  local root="$1"
  local skill="$2"
  local dir="$root/$skill"

  if [[ -d "$dir" ]]; then
    run_cmd rm -rf "$dir"
    log "remove $skill"
  else
    log "skip   $dir (not found)"
  fi
}

verify_skill() {
  local root="$1"
  local skill="$2"
  local dir="$root/$skill"
  local file="$dir/SKILL.md"

  [[ -d "$dir" ]] || { log "verify fail $skill: missing dir"; return 1; }
  [[ -f "$file" ]] || { log "verify fail $skill: missing SKILL.md"; return 1; }
  grep -q '^---$' "$file" || { log "verify fail $skill: missing frontmatter"; return 1; }
  grep -q "^name: $skill$" "$file" || { log "verify fail $skill: missing/invalid name"; return 1; }
  grep -q '^description: ' "$file" || { log "verify fail $skill: missing description"; return 1; }

  if [[ "$WITHOUT_SUPPORT_FILES" -ne 1 ]]; then
    [[ -f "$dir/template.md" ]] || { log "verify fail $skill: missing template.md"; return 1; }
    [[ -d "$dir/examples" ]] || { log "verify fail $skill: missing examples dir"; return 1; }
  fi

  log "verify ok   $skill"
}

copy_skill_dir() {
  local src="$1"
  local dst_root="$2"
  local skill_name
  skill_name="$(basename "$src")"

  [[ -d "$src" ]] || return 0
  [[ -f "$src/SKILL.md" ]] || return 0

  if [[ -d "$dst_root/$skill_name" && "$FORCE" -ne 1 ]]; then
    log "skip   $dst_root/$skill_name (exists, use --force to overwrite)"
    return 0
  fi

  if [[ "$DRY_RUN" -eq 1 ]]; then
    log "[dry-run] import $src -> $dst_root/$skill_name"
  else
    rm -rf "$dst_root/$skill_name"
    mkdir -p "$dst_root"
    cp -R "$src" "$dst_root/$skill_name"
  fi

  log "import $skill_name"
}

import_from_dir() {
  local src_root="$1"
  local dst_root="$2"

  [[ -d "$src_root" ]] || err "Import dir not found: $src_root"

  local found=0
  local d
  for d in "$src_root"/*; do
    [[ -d "$d" ]] || continue
    [[ -f "$d/SKILL.md" ]] || continue
    copy_skill_dir "$d" "$dst_root"
    found=1
  done

  [[ "$found" -eq 1 ]] || err "No skill folders with SKILL.md found in: $src_root"
}

import_from_github() {
  local repo_url="$1"
  local dst_root="$2"
  local tmp

  need_cmd git

  tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' RETURN

  if [[ "$DRY_RUN" -eq 1 ]]; then
    log "[dry-run] git clone $repo_url $tmp/repo"
    return 0
  fi

  git clone --depth 1 "$repo_url" "$tmp/repo" >/dev/null 2>&1 || err "Failed to clone: $repo_url"

  if [[ -d "$tmp/repo/.claude/skills" ]]; then
    import_from_dir "$tmp/repo/.claude/skills" "$dst_root"
  elif [[ -d "$tmp/repo/skills" ]]; then
    import_from_dir "$tmp/repo/skills" "$dst_root"
  else
    local found
    found="$(find "$tmp/repo" -mindepth 2 -maxdepth 4 -type f -name SKILL.md | head -n 1 || true)"
    [[ -n "$found" ]] || err "No skills found in cloned repo"
    import_from_dir "$(dirname "$(dirname "$found")")" "$dst_root"
  fi
}

print_list() {
  cat <<EOF
Supported targets:
  - claude
  - windsurf

Default target:
  - claude

Scopes:
  - global
  - workspace

Install roots:
  - claude global:      ~/.claude/skills
  - claude workspace:   ./.claude/skills
  - windsurf global:    ~/.codeium/windsurf/skills
  - windsurf workspace: ./.windsurf/skills

Bundles:
  - core
  - backend
  - frontend
  - fullstack
  - all

Core skills:
$(skills_for_bundle core | sed 's/^/  - /')

Usage after install:
  Claude:
    /planner
    /code-review
    /debug

  Windsurf:
    @planner
    @code-review
    @debug
EOF
}

validate_args() {
  case "$TARGET" in
    claude|windsurf) ;;
    *) err "Invalid --target: $TARGET" ;;
  esac

  case "$SCOPE" in
    global|workspace) ;;
    *) err "Invalid --scope: $SCOPE" ;;
  esac

  case "$BUNDLE" in
    core|backend|frontend|fullstack|all) ;;
    *) err "Invalid --bundle: $BUNDLE" ;;
  esac
}

parse_args() {
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --target) TARGET="${2:-}"; shift 2 ;;
      --scope) SCOPE="${2:-}"; shift 2 ;;
      --bundle) BUNDLE="${2:-}"; shift 2 ;;
      --import-github) IMPORT_GITHUB="${2:-}"; shift 2 ;;
      --import-dir) IMPORT_DIR="${2:-}"; shift 2 ;;
      --without-support-files) WITHOUT_SUPPORT_FILES=1; shift ;;
      --verify) VERIFY=1; shift ;;
      --dry-run) DRY_RUN=1; shift ;;
      --force) FORCE=1; shift ;;
      --uninstall) UNINSTALL=1; shift ;;
      --self-test) SELF_TEST=1; shift ;;
      --list) LIST_ONLY=1; shift ;;
      -h|--help) usage; exit 0 ;;
      *) err "Unknown argument: $1" ;;
    esac
  done
}

self_test() {
  local tmp root skill ok=1
  tmp="$(mktemp -d)"
  root="$tmp/skills"

  log "self-test root: $root"

  while IFS= read -r skill; do
    write_skill "$root" "$skill"
  done < <(skills_for_bundle all)

  while IFS= read -r skill; do
    if ! verify_skill "$root" "$skill"; then
      ok=0
    fi
  done < <(skills_for_bundle all)

  rm -rf "$tmp"

  if [[ "$ok" -eq 1 ]]; then
    log "self-test passed"
  else
    err "self-test failed"
  fi
}

main() {
  parse_args "$@"
  validate_args

  if [[ "$LIST_ONLY" -eq 1 ]]; then
    print_list
    exit 0
  fi

  if [[ "$SELF_TEST" -eq 1 ]]; then
    self_test
    exit 0
  fi

  local root
  root="$(target_root)"

  if [[ "$DRY_RUN" -eq 1 ]]; then
    log "target: $TARGET"
    log "scope:  $SCOPE"
    log "bundle: $BUNDLE"
    log "root:   $root"
  fi

  run_cmd mkdir -p "$root"

  if [[ "$UNINSTALL" -eq 1 ]]; then
    while IFS= read -r skill; do
      remove_skill "$root" "$skill"
    done < <(skills_for_bundle "$BUNDLE")
    exit 0
  fi

  if [[ -n "$IMPORT_DIR" ]]; then
    import_from_dir "$IMPORT_DIR" "$root"
  fi

  if [[ -n "$IMPORT_GITHUB" ]]; then
    import_from_github "$IMPORT_GITHUB" "$root"
  fi

  while IFS= read -r skill; do
    write_skill "$root" "$skill"
  done < <(skills_for_bundle "$BUNDLE")

  if [[ "$VERIFY" -eq 1 ]]; then
    while IFS= read -r skill; do
      verify_skill "$root" "$skill"
    done < <(skills_for_bundle "$BUNDLE")
  fi

  cat <<EOF

Done.

Target: $TARGET
Scope:  $SCOPE
Root:   $root
Bundle: $BUNDLE

Installed skills:
$(skills_for_bundle "$BUNDLE" | sed 's/^/  - /')

How to use:
EOF

  local prefix
  prefix="$(manual_prefix)"
  if [[ -n "$prefix" ]]; then
    cat <<EOF
  ${prefix}planner
  ${prefix}architect
  ${prefix}code-review
  ${prefix}debug
EOF
  else
    cat <<'EOF'
  Use natural language so the agent auto-selects the matching skill.
EOF
  fi
}

main "$@"
