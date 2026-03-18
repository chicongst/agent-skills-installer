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

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUNDLED_SKILLS_DIR="$SCRIPT_DIR/skills"

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
architect
code-review
debug
refactor
test-writer
security-review
docs-writer
api-design
algorithm-review
mastery
EOF
      ;;
    backend)
      cat <<'EOF'
architect
code-review
debug
refactor
test-writer
security-review
docs-writer
api-design
db-design
migration-safety
sre-engineering
performance-review
algorithm-review
mastery
EOF
      ;;
    frontend)
      cat <<'EOF'
architect
code-review
debug
refactor
test-writer
security-review
docs-writer
api-design
algorithm-review
mastery
EOF
      ;;
    fullstack)
      cat <<'EOF'
architect
code-review
debug
refactor
test-writer
security-review
docs-writer
api-design
db-design
migration-safety
sre-engineering
performance-review
pr-review
changelog
algorithm-review
mastery
EOF
      ;;
    all)
      cat <<'EOF'
architect
code-review
debug
refactor
test-writer
security-review
docs-writer
api-design
db-design
migration-safety
sre-engineering
performance-review
pr-review
changelog
algorithm-review
mastery
EOF
      ;;
    *)
      err "Unknown bundle: $1"
      ;;
  esac
}

skill_description() {
  local skill="$1"
  local file="$BUNDLED_SKILLS_DIR/$skill/SKILL.md"
  if [[ -f "$file" ]]; then
    grep '^description: ' "$file" | head -1 | sed 's/^description: //'
  else
    echo "General-purpose engineering skill."
  fi
}


skill_dir_exists() {
  local dir="$1"
  [[ -d "$dir" ]]
}

write_skill() {
  local root="$1"
  local skill="$2"
  local src="$BUNDLED_SKILLS_DIR/$skill"
  local dst="$root/$skill"

  if [[ ! -d "$src" ]]; then
    err "Bundled skill not found: $skill (expected at $src)"
  fi
  if [[ ! -f "$src/SKILL.md" ]]; then
    err "Bundled skill missing SKILL.md: $src/SKILL.md"
  fi

  if [[ -d "$dst" && "$FORCE" -ne 1 ]]; then
    log "skip   $dst (exists, use --force to overwrite)"
    return 0
  fi

  if [[ "$DRY_RUN" -eq 1 ]]; then
    log "[dry-run] install $skill from $src"
    return 0
  fi

  run_cmd mkdir -p "$dst"
  run_cmd cp "$src/SKILL.md" "$dst/SKILL.md"

  if [[ "$WITHOUT_SUPPORT_FILES" -ne 1 ]]; then
    if [[ -f "$src/template.md" ]]; then
      run_cmd cp "$src/template.md" "$dst/template.md"
    fi
    if [[ -d "$src/examples" ]]; then
      run_cmd cp -r "$src/examples" "$dst/examples"
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
    /architect
    /code-review
    /debug

  Windsurf:
    @architect
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
  ${prefix}architect
  ${prefix}code-review
  ${prefix}debug
  ${prefix}mastery
EOF
  else
    cat <<'EOF'
  Use natural language so the agent auto-selects the matching skill.
EOF
  fi
}

main "$@"
