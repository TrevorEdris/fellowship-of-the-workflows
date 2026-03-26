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

# --- Resolve agent from SKILL.md frontmatter ---
# Parse the agent: field from between the --- fences
AGENT_NAME=$(sed -n '/^---$/,/^---$/{ s/^agent: *//p; }' "$SKILL_MD" | tr -d ' "'"'"'')
SYSTEM_PROMPT=""

if [[ -n "$AGENT_NAME" ]]; then
  AGENT_FILE="$REPO_ROOT/agents/${AGENT_NAME}.md"
  if [[ -f "$AGENT_FILE" ]]; then
    # Agent first (persona/methodology), then skill (task instructions)
    SYSTEM_PROMPT="$(cat "$AGENT_FILE")"$'\n\n'"$(cat "$SKILL_MD")"
  else
    echo "WARN: Agent '$AGENT_NAME' referenced but $AGENT_FILE not found" >&2
    SYSTEM_PROMPT="$(cat "$SKILL_MD")"
  fi
else
  SYSTEM_PROMPT="$(cat "$SKILL_MD")"
fi

# --bare skips hooks/LSP/plugin overhead for faster eval runs
# --dangerously-skip-permissions avoids interactive prompts during eval
# --add-dir gives the model Read access to skill references, assets, etc.
claude -p \
  --model "$MODEL" \
  --system-prompt "$SYSTEM_PROMPT" \
  --dangerously-skip-permissions \
  --bare \
  --add-dir "$SKILL_DIR" \
  --output-format text \
  "$PROMPT" 2>/dev/null
