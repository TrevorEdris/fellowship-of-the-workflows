#!/usr/bin/env bash
# Run a skill against a single test prompt and capture the output.
#
# Sets up a native workspace so the model can Read reference files and
# receives the agent persona (if any) prepended to the system prompt.
#
# Usage: ./run-skill-eval.sh <skill_name> <prompt_file> <model>
# Output: Skill output written to stdout

set -euo pipefail

SKILL_NAME="$1"
PROMPT_FILE="$2"
MODEL="${3:-sonnet}"

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
SKILL_DIR="$REPO_ROOT/skills/$SKILL_NAME"
SKILL_MD="$SKILL_DIR/SKILL.md"

if [[ ! -f "$SKILL_MD" ]]; then
  echo "ERROR: SKILL.md not found at $SKILL_MD" >&2
  exit 1
fi

if [[ ! -f "$PROMPT_FILE" ]]; then
  echo "ERROR: Prompt file not found: $PROMPT_FILE" >&2
  exit 1
fi

PROMPT=$(cat "$PROMPT_FILE")

SYSTEM_PROMPT="$(cat "$SKILL_MD")"

# --dangerously-skip-permissions avoids interactive prompts during eval
# --add-dir gives the model Read access to skill references, assets, agent files, etc.
# Note: --bare is intentionally omitted; it requires ANTHROPIC_API_KEY and
# bypasses subscription/OAuth auth (keychain). Without it, normal auth applies.
claude -p \
  --model "$MODEL" \
  --system-prompt "$SYSTEM_PROMPT" \
  --dangerously-skip-permissions \
  --add-dir "$SKILL_DIR" \
  --add-dir "$REPO_ROOT/agents" \
  --output-format text \
  "$PROMPT" 2>/dev/null
