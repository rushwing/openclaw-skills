#!/usr/bin/env bash
# package_skill.sh — Package an OpenClaw skill into a deployable zip
#
# Usage:
#   ./scripts/package_skill.sh <skill-name>
#
# Output:
#   dist/<skill-name>.zip

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SKILLS_DIR="$REPO_ROOT/skills"
DIST_DIR="$REPO_ROOT/dist"

# ── Argument check ─────────────────────────────────────────────────────────────
if [ $# -ne 1 ]; then
  echo "Usage: $0 <skill-name>"
  exit 1
fi

SKILL_NAME="$1"
SKILL_DIR="$SKILLS_DIR/$SKILL_NAME"

if [ ! -d "$SKILL_DIR" ]; then
  echo "ERROR: Skill '$SKILL_NAME' not found at $SKILL_DIR"
  exit 1
fi

if [ ! -f "$SKILL_DIR/SKILL.md" ]; then
  echo "ERROR: Missing SKILL.md in $SKILL_DIR"
  exit 1
fi

# ── Prepare dist/ ──────────────────────────────────────────────────────────────
mkdir -p "$DIST_DIR"
OUTPUT="$DIST_DIR/${SKILL_NAME}.zip"

# ── Package ────────────────────────────────────────────────────────────────────
# Zip with skill name as root directory inside the archive,
# excluding macOS/editor artifacts
(
  cd "$SKILLS_DIR"
  zip -r "$OUTPUT" "$SKILL_NAME" \
    --exclude "*/.DS_Store" \
    --exclude "*/__pycache__/*" \
    --exclude "*/*.pyc" \
    --exclude "*/.claude/*"
)

echo "Packaged: $OUTPUT"
