#!/usr/bin/env bash
# FOTW Autoresearch — Run a single eval iteration for a target.
#
# Usage:
#   ./evals/autoresearch.sh <target_name>                          # Run one eval iteration
#   ./evals/autoresearch.sh <target_name> --baseline               # Establish baseline
#   ./evals/autoresearch.sh <target_name> --report                 # Show results.tsv
#   ./evals/autoresearch.sh <target_name> --dashboard              # Open visual dashboard
#   ./evals/autoresearch.sh <target_name> --describe "what changed" # Tag the run
#
# For the full autonomous loop, use autoresearch-program.md with a
# long-lived Claude session (Option D):
#
#   claude --dangerously-skip-permissions \
#     --system-prompt "$(cat evals/autoresearch-program.md)" \
#     "Run autoresearch on <target_name>"

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
EVALS_DIR="$REPO_ROOT/evals"
SHARED_DIR="$EVALS_DIR/shared"

# --- Parse args ---
TARGET_NAME="${1:?Usage: autoresearch.sh <target_name> [--baseline|--report|--describe \"desc\"]}"
shift

MODE="eval"
DESCRIPTION="eval run"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --baseline) MODE="baseline"; DESCRIPTION="baseline"; shift ;;
    --report) MODE="report"; shift ;;
    --dashboard) MODE="dashboard"; shift ;;
    --describe) DESCRIPTION="$2"; shift 2 ;;
    *) echo "Unknown option: $1" >&2; exit 1 ;;
  esac
done

TARGET_DIR="$EVALS_DIR/targets/$TARGET_NAME"
CONFIG_FILE="$TARGET_DIR/config.yaml"
RESULTS_FILE="$TARGET_DIR/results.tsv"

if [[ ! -d "$TARGET_DIR" ]]; then
  echo "ERROR: Target not found: $TARGET_DIR" >&2
  echo "Available targets:" >&2
  ls "$EVALS_DIR/targets/" 2>/dev/null || echo "  (none)" >&2
  exit 1
fi

# --- Report mode ---
if [[ "$MODE" == "report" ]]; then
  if [[ -f "$RESULTS_FILE" ]]; then
    echo "=== Results for $TARGET_NAME ==="
    column -t -s $'\t' "$RESULTS_FILE"
  else
    echo "No results yet for $TARGET_NAME"
  fi
  exit 0
fi

# --- Dashboard mode ---
if [[ "$MODE" == "dashboard" ]]; then
  PYTHON=$(command -v python3 || echo "$REPO_ROOT/cli/.venv/bin/python")
  "$PYTHON" "$EVALS_DIR/dashboard.py" "$TARGET_NAME"
  exit 0
fi

if [[ ! -f "$CONFIG_FILE" ]]; then
  echo "ERROR: config.yaml not found in $TARGET_DIR" >&2
  exit 1
fi

# --- Parse config.yaml (simple grep, no yq dependency) ---
yaml_val() {
  grep "^${1}:" "$CONFIG_FILE" | head -1 | sed "s/^${1}: *//" | tr -d '"' | tr -d "'"
}

SKILL_NAME=$(yaml_val "name")
TARGET_TYPE=$(yaml_val "type")
RUNS_PER_ITERATION=$(yaml_val "runs_per_iteration")
SKILL_MODEL=$(yaml_val "model")
JUDGE_MODEL=$(yaml_val "judge_model")
FALLBACK_MODEL=$(yaml_val "fallback_model")

RUNS_PER_ITERATION="${RUNS_PER_ITERATION:-5}"
SKILL_MODEL="${SKILL_MODEL:-sonnet}"
JUDGE_MODEL="${JUDGE_MODEL:-sonnet}"
FALLBACK_MODEL="${FALLBACK_MODEL:-opus}"

# --- Initialize results.tsv if needed ---
if [[ ! -f "$RESULTS_FILE" ]]; then
  printf "commit\tscore\tmax_score\tpass_rate\tstatus\tdescription\n" > "$RESULTS_FILE"
fi

# --- Collect prompt files ---
PROMPT_DIR="$TARGET_DIR/prompts"
PROMPT_FILES=()
for f in "$PROMPT_DIR"/*.md; do
  [[ -f "$f" ]] && PROMPT_FILES+=("$f")
done

if [[ ${#PROMPT_FILES[@]} -eq 0 ]]; then
  echo "ERROR: No prompt files found in $PROMPT_DIR" >&2
  exit 1
fi

# --- Count criteria ---
CRITERIA_COUNT=$(grep -c "^  - id:" "$TARGET_DIR/criteria.yaml" 2>/dev/null || echo "0")
if [[ "$CRITERIA_COUNT" -eq 0 ]]; then
  echo "ERROR: No criteria found in $TARGET_DIR/criteria.yaml" >&2
  exit 1
fi

NUM_PROMPTS=${#PROMPT_FILES[@]}
MAX_SCORE=$((RUNS_PER_ITERATION * NUM_PROMPTS * CRITERIA_COUNT))

echo "=== FOTW Autoresearch: $TARGET_NAME ==="
echo "Type: $TARGET_TYPE | Model: $SKILL_MODEL | Judge: $JUDGE_MODEL | Fallback: $FALLBACK_MODEL"
echo "Prompts: $NUM_PROMPTS | Runs/prompt: $RUNS_PER_ITERATION | Criteria: $CRITERIA_COUNT"
echo "Max possible score: $MAX_SCORE"
echo ""

# --- Run eval ---
TOTAL_PASS=0
TOTAL_JUDGMENTS=0
TMPDIR=$(mktemp -d)
trap "rm -rf $TMPDIR" EXIT

# Per-criterion tracking via flat file: each line is "criterion_id PASS" or "criterion_id FAIL"
CRITERION_LOG="$TMPDIR/criterion_log.txt"
touch "$CRITERION_LOG"

for prompt_file in "${PROMPT_FILES[@]}"; do
  prompt_name=$(basename "$prompt_file" .md)
  echo "--- Prompt: $prompt_name ---"

  for run in $(seq 1 "$RUNS_PER_ITERATION"); do
    echo -n "  Run $run/$RUNS_PER_ITERATION... "

    OUTPUT_FILE="$TMPDIR/${prompt_name}_run${run}.txt"
    JUDGE_FILE="$TMPDIR/${prompt_name}_run${run}_judge.txt"

    # Run skill, with fallback on failure
    if ! "$SHARED_DIR/run-skill-eval.sh" "$SKILL_NAME" "$prompt_file" "$SKILL_MODEL" > "$OUTPUT_FILE" 2>/dev/null; then
      echo -n "(fallback:$FALLBACK_MODEL) "
      if ! "$SHARED_DIR/run-skill-eval.sh" "$SKILL_NAME" "$prompt_file" "$FALLBACK_MODEL" > "$OUTPUT_FILE" 2>/dev/null; then
        echo "SKIP (invocation failed)"
        continue
      fi
    fi

    # Check for empty output
    if [[ ! -s "$OUTPUT_FILE" ]]; then
      echo "SKIP (empty output)"
      continue
    fi

    # Judge output
    if ! "$SHARED_DIR/score-output.sh" "$TARGET_DIR" "$OUTPUT_FILE" "$JUDGE_MODEL" > "$JUDGE_FILE" 2>/dev/null; then
      echo "SKIP (judge failed)"
      continue
    fi

    # Parse judge output — count criterion PASS/FAIL lines
    # Format: "criterion_id: PASS | reason" or "criterion_id: FAIL | reason"
    # Judge may wrap lines in code fences or add leading whitespace
    RUN_PASS=0
    while IFS= read -r line; do
      # Strip leading whitespace, backticks, and markdown formatting
      cleaned=$(echo "$line" | sed 's/^[[:space:]`]*//')
      cid=$(echo "$cleaned" | sed -n 's/^\([a-z_][a-z_]*\): *PASS.*/\1/p')
      if [[ -n "$cid" ]]; then
        RUN_PASS=$((RUN_PASS + 1))
        echo "$cid PASS" >> "$CRITERION_LOG"
      fi
      cid=$(echo "$cleaned" | sed -n 's/^\([a-z_][a-z_]*\): *FAIL.*/\1/p')
      if [[ -n "$cid" ]]; then
        echo "$cid FAIL" >> "$CRITERION_LOG"
      fi
    done < "$JUDGE_FILE"

    TOTAL_PASS=$((TOTAL_PASS + RUN_PASS))
    TOTAL_JUDGMENTS=$((TOTAL_JUDGMENTS + CRITERIA_COUNT))

    echo "$RUN_PASS/$CRITERIA_COUNT"
  done
done

# --- Compute aggregate ---
if [[ $TOTAL_JUDGMENTS -gt 0 ]]; then
  PASS_RATE=$(awk "BEGIN {printf \"%.1f\", ($TOTAL_PASS / $TOTAL_JUDGMENTS) * 100}")
else
  PASS_RATE="0.0"
fi

echo ""
echo "=== TOTAL: $TOTAL_PASS/$TOTAL_JUDGMENTS ($PASS_RATE%) ==="
echo ""

# --- Per-criterion breakdown ---
echo "Per-criterion breakdown:"
if [[ -s "$CRITERION_LOG" ]]; then
  # Get unique criterion IDs, then count PASS/total for each
  for cid in $(awk '{print $1}' "$CRITERION_LOG" | sort -u); do
    total=$(grep -c "^$cid " "$CRITERION_LOG" 2>/dev/null) || total=0
    passes=$(grep -c "^$cid PASS" "$CRITERION_LOG" 2>/dev/null) || passes=0
    if [[ $total -gt 0 ]]; then
      rate=$(awk "BEGIN {printf \"%.0f\", ($passes / $total) * 100}")
      echo "  $cid: $passes/$total ($rate%)"
    fi
  done
fi
echo ""

# --- Log to results.tsv ---
COMMIT=$(cd "$REPO_ROOT" && git rev-parse --short HEAD 2>/dev/null || echo "unknown")

if [[ "$MODE" == "baseline" ]]; then
  STATUS="keep"
else
  STATUS="pending"
fi

printf "%s\t%d\t%d\t%s%%\t%s\t%s\n" \
  "$COMMIT" "$TOTAL_PASS" "$TOTAL_JUDGMENTS" "$PASS_RATE" "$STATUS" "$DESCRIPTION" \
  >> "$RESULTS_FILE"

echo "Logged to $RESULTS_FILE"

# --- Machine-readable output for the autoresearch agent ---
echo ""
echo "AUTORESEARCH_SCORE=$TOTAL_PASS"
echo "AUTORESEARCH_MAX=$TOTAL_JUDGMENTS"
echo "AUTORESEARCH_RATE=$PASS_RATE"
