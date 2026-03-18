#!/usr/bin/env bash
set -euo pipefail

REPO_OWNER="chicongst"
REPO_NAME="agent-skills-installer"
BRANCH="main"

TARBALL_URL="https://github.com/${REPO_OWNER}/${REPO_NAME}/archive/refs/heads/${BRANCH}.tar.gz"

TMP_DIR=$(mktemp -d)
trap 'rm -rf "$TMP_DIR"' EXIT

echo "Downloading agent-skills-installer..."

curl -fsSL "$TARBALL_URL" -o "$TMP_DIR/repo.tar.gz"

tar -xzf "$TMP_DIR/repo.tar.gz" -C "$TMP_DIR"

REPO_DIR="$TMP_DIR/${REPO_NAME}-${BRANCH}"

chmod +x "$REPO_DIR/setup_agent_skills.sh"

echo "Running installer..."

"$REPO_DIR/setup_agent_skills.sh" "$@"
