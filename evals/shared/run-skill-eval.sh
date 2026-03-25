#!/usr/bin/env bash
# Run a skill against a single test prompt and capture the output.
#
# Usage: ./run-skill-eval.sh <skill_name> <prompt_file> <model>
# Output: Skill output written to stdout

set -euo pipefail

SKILL_NAME="$1"
PROMPT_FILE="$2"
MODEL="${3:-sonnet}"

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
SKILL_MD="$REPO_ROOT/skills/$SKILL_NAME/SKILL.md"

if [[ ! -f "$SKILL_MD" ]]; then
  echo "ERROR: SKILL.md not found at $SKILL_MD" >&2
  exit 1
fi

if [[ ! -f "$PROMPT_FILE" ]]; then
  echo "ERROR: Prompt file not found: $PROMPT_FILE" >&2
  exit 1
fi

PROMPT=$(cat "$PROMPT_FILE")

# --bare skips hooks/LSP/plugin overhead for faster eval runs
# --dangerously-skip-permissions avoids interactive prompts during eval
claude -p \
  --model "$MODEL" \
  --system-prompt "$(cat "$SKILL_MD")" \
  --dangerously-skip-permissions \
  --bare \
  --output-format text \
  "$PROMPT" 2>/dev/null
