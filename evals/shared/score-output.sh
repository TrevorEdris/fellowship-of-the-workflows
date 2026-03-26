#!/usr/bin/env bash
# Score a skill's output against binary criteria using an LLM judge.
#
# Usage: ./score-output.sh <target_dir> <output_file> <judge_model>
# Output: Judge response to stdout (parseable PASS/FAIL lines + TOTAL)

set -euo pipefail

TARGET_DIR="$1"
OUTPUT_FILE="$2"
JUDGE_MODEL="${3:-sonnet}"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
JUDGE_SYSTEM="$SCRIPT_DIR/judge-system-prompt.md"
CRITERIA_FILE="$TARGET_DIR/criteria.yaml"
JUDGE_CONTEXT="$TARGET_DIR/judge-context.md"

if [[ ! -f "$CRITERIA_FILE" ]]; then
  echo "ERROR: criteria.yaml not found in $TARGET_DIR" >&2
  exit 1
fi

SKILL_OUTPUT=$(cat "$OUTPUT_FILE")
CRITERIA=$(cat "$CRITERIA_FILE")
CONTEXT=""
if [[ -f "$JUDGE_CONTEXT" ]]; then
  CONTEXT=$(cat "$JUDGE_CONTEXT")
fi

JUDGE_PROMPT="## Skill Output

$SKILL_OUTPUT

## Evaluation Criteria

$CRITERIA

## Ground Truth Context

$CONTEXT

## Instructions

Score each criterion as PASS or FAIL. Follow the format exactly."

claude -p \
  --model "$JUDGE_MODEL" \
  --system-prompt "$(cat "$JUDGE_SYSTEM")" \
  --dangerously-skip-permissions \
  --output-format text \
  "$JUDGE_PROMPT" 2>/dev/null
