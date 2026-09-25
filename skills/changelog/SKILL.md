---
name: changelog
description: Use when turning commits, merged PRs, or a git range into CHANGELOG.md entries or release notes — classifies changes with Keep a Changelog categories, flags breaking changes and SemVer mismatches, and produces a developer changelog plus user-facing release notes without inventing facts. Not for writing guides, migration docs, or API references (use `docs-writer`), deciding whether a release is safe to ship (use `release-readiness`), or designing an API versioning policy (use `api-design`).
---

# Changelog

Turn a set of changes into an accurate, scannable changelog. Every line must trace back to a commit, PR, issue, diff, or something the user said.

## Critical Rules

1. **No invented facts.** Never make up versions, dates, PR/issue numbers, percentages, timings, UI locations, commands, removal dates, dependency versions, known issues, or links. If a detail is needed but not in the sources, write `[UNKNOWN: what is missing]` and add it to Open Questions. Reading the diff counts as a source; your expectation of what a change "probably" does does not.
2. **Breaking changes are never hidden** — marked, migrated, and surfaced (Steps 2 and 5).
3. **Never silently rename the version** — flag a SemVer mismatch and ask (Step 4).
4. **Symptoms, not code.** "Profile update no longer fails when the name contains é", not "fix encoding in updateProfile()".
5. **Never guess an unclear commit into a category** (Step 3).
6. **Project convention wins.** If the repo already has a `CHANGELOG.md`, match its headings, category names, and entry style; prepend the new section and never rewrite past entries. Only write to the file if the user asks; otherwise print the output.

## Step 1 — Gather Input

Establish the range, then collect sources. If you cannot run commands, ask the user to paste the commit list or PR list (use AskUserQuestion if available, otherwise ask in plain text).

```bash
git describe --tags --abbrev=0                       # last tag = start of range (confirm with user if HEAD is already tagged)
git log v1.4.0..HEAD --no-merges --format='%h %s'    # subjects in range
git log v1.4.0..HEAD --format='--- %h %s%n%b'        # with bodies (BREAKING CHANGE footers, "Closes #N")
git log v1.4.0..HEAD --format='%h %s' | grep -E '^[0-9a-f]+ [a-z]+(\([^)]*\))?!:'   # "!" breaking markers
git log v1.4.0..HEAD -E --grep='^BREAKING[ -]CHANGE' --format='%h %s'               # footer breaking markers
gh pr list --state merged --base main --search "merged:>=2024-03-01" \
  --json number,title,labels,body --limit 200         # PR titles, labels, bodies (GitHub)
```

Also collect: the requested version and release date (ask if missing), and whether the product's readers are end users or developers (library/API/CLI — then the release notes section may be skipped if the user agrees).

**No version yet:** use `# Changelog: Unreleased` (date `UNKNOWN`) and `## [Unreleased]` as the Keep a Changelog heading, and write the Version check as `Unreleased — requires {bump} (next: {X.Y.Z} after {last tag})`.

## Step 2 — Classify

One category system: **Keep a Changelog** — `Added`, `Changed`, `Deprecated`, `Removed`, `Fixed`, `Security`, in that order. Classify by the effect on the reader, not by the commit type; the table is the starting point.

| Signal (Conventional Commit type / PR label) | Category |
|---|---|
| `feat` / `feature`, `enhancement` | Added (new capability) or Changed (change to existing behavior) |
| `fix` / `bug` | Fixed (Security if it fixes a vulnerability) |
| `perf` | Changed — include numbers only if the source measured them, with their context |
| `build(deps)` / `dependencies` | Changed, or Security if the source cites a CVE/advisory |
| Text says "deprecate" (any type, even `chore`) | Deprecated — include replacement and removal version, or `[UNKNOWN]` |
| Text says "remove", "drop support" | Removed — almost always BREAKING |
| `!` after type, `BREAKING CHANGE:` footer, `breaking` label | BREAKING, in the category that fits (often Changed/Removed) |
| `refactor`, `test`, `ci`, `style`, `docs`, `chore` with no user-visible effect | Excluded (list under Excluded with a reason) |
| A commit and its revert both in range | Exclude both |

**What counts as breaking** (even without a marker): removing or renaming a public API, endpoint, field, CLI flag, config key, or event; changing a response shape, type, or default behavior; raising the minimum runtime/platform version. The "public API" is whatever the project declares; if it is undeclared, treat anything external consumers can call as public and say so. If a diff touches a public surface and you cannot tell whether it stays compatible, list it in Open Questions as "possibly breaking — confirm".

## Step 3 — Ambiguous Commits

For a subject like "fix stuff", "update", "WIP", or a squash that mixes several changes:

1. Read the PR title, body, and linked issue.
2. Read the diff: `git show --stat <sha>`, then `git show <sha>` for the files that matter.
3. If the effect is now clear, classify it and describe the symptom the diff supports — nothing more.
4. If it is still unclear, leave it out of every category. Add it to Open Questions with the SHA, what you found (files touched), and the specific question. Split a squash that mixes changes into separate entries only when each part is identifiable.

## Step 4 — SemVer Check

| Contents | Required bump (≥ 1.0.0) |
|---|---|
| Any BREAKING entry | **major** (x.0.0) |
| Added, Deprecated, or a Changed entry that alters visible behavior | minor (1.x.0) |
| Only Fixed / Security / internal Changed (perf, deps, no visible behavior change) | patch (1.4.x) |

For `0.y.z`, SemVer allows anything to change; the common convention is breaking ⇒ bump `y` — state which you applied. If the requested version is too low, keep it, put `⚠ MISMATCH` in the Version check line naming the entries that force the bump, and make it Open Question 1 with both options (bump the version, or make the change non-breaking). A higher bump than required is fine.

## Step 5 — Write the Entries

- One line per change: what changed for the reader, then the reference `(#PR)` or short SHA if there is no PR. Area prefix optional; match the repo.
- Several commits/PRs implementing one change → one entry citing all refs, e.g. `(#12, #15)`.
- BREAKING entries start with `**BREAKING:**`, come first in their category, and carry `Migration:` with the exact step from the source (or `[UNKNOWN: migration]`).
- Deprecations name the replacement and the removal version, or `[UNKNOWN]`.
- Release notes use plain language for end users and drop internal-only entries (dependency bumps, tooling) unless they change something users see.

**Release notes mapping** (user-facing labels are derived, never classified separately):

| Developer category | Release notes section |
|---|---|
| Any BREAKING entry, Removed, Deprecated | ⚠ Action required |
| Added | New |
| Changed (non-breaking) | Improved |
| Fixed | Fixed |
| Security | Security |

## Output Format

A worked example is in `examples/example.txt` (if installed). `template.md` mirrors this format.

```markdown
# Changelog: [version] — [YYYY-MM-DD | UNKNOWN]

**Range**: [from]..[to] — [N] commits, [M] PRs
**Version check**: [OK — requires {major|minor|patch} | ⚠ MISMATCH — {entries} are breaking; SemVer requires {X.0.0} | Unreleased — requires {bump} (next: {X.Y.Z} after {last tag})]

## Developer Changelog

## [version] - [YYYY-MM-DD]

### Added
- [Change] (#PR)

### Changed
- [Change] (#PR)

### Deprecated
- [What] — use [replacement]. Removal: [version | UNKNOWN] (#PR)

### Removed
- **BREAKING:** [What was removed]. Migration: [step] (#PR)

### Fixed
- [Symptom that no longer occurs] (#PR)

### Security
- [Vulnerability addressed, CVE/advisory if given] (#PR)

## Release Notes

### ⚠ Action required
- [Who is affected and what they must do]

### New
- [Plain-language description]

### Improved
- [Plain-language description]

### Fixed
- [Plain-language description]

### Security
- [Plain-language description]

## Open Questions
1. [Question — SHA/PR, what is known, what is needed]

## Excluded
- [SHA or #PR] [subject] — [reason]
```

Omit any empty category or section instead of writing "none". BREAKING entries may appear in any developer category, not only Removed. The `## [version] - [date]` block is kept at H2 so it pastes verbatim into `CHANGELOG.md`.
