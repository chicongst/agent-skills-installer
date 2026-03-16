#!/usr/bin/env bash
set -e

REPO="https://raw.githubusercontent.com/chicongst/agent-skills-installer/main"

TMP_DIR=$(mktemp -d)

echo "Downloading installer..."

curl -fsSL "$REPO/setup_agent_skills.sh" -o "$TMP_DIR/setup_agent_skills.sh"

chmod +x "$TMP_DIR/setup_agent_skills.sh"

echo "Running installer..."

"$TMP_DIR/setup_agent_skills.sh" "$@"

rm -rf "$TMP_DIR"
