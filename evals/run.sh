#!/usr/bin/env bash
# Launch an autonomous autoresearch optimization session.
#
# Usage:
#   ./evals/run.sh <target>                   # Start loop (unlimited iterations)
#   ./evals/run.sh <target> -n 10             # Run 10 iterations then stop
#   ./evals/run.sh <target> --dry-run         # Validate config, don't launch
#   ./evals/run.sh <target> --model opus      # Override loop agent model
#   ./evals/run.sh <target> --no-branch       # Skip git branch creation
#   ./evals/run.sh <target> --no-baseline     # Skip baseline check

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
EVALS_DIR="$REPO_ROOT/evals"
PROGRAM_MD="$EVALS_DIR/autoresearch-program.md"

# --- Defaults ---
MODEL="opus"
ITERATIONS=""
CREATE_BRANCH=true
RUN_BASELINE=true
DRY_RUN=false

# --- Usage ---
usage() {
  echo "Usage: ./evals/run.sh <target> [options]"
  echo ""
  echo "Launch an autonomous autoresearch optimization session."
  echo ""
  echo "Options:"
  echo "  -n <count>     Max iterations (default: unlimited)"
  echo "  --model <name> Model for the loop agent (default: opus)"
  echo "  --no-branch    Skip git branch creation"
  echo "  --no-baseline  Skip baseline check"
  echo "  --dry-run      Validate config and exit"
  echo "  -h, --help     Show this help"
  echo ""
  echo "Available targets:"
  for d in "$EVALS_DIR/targets"/*/; do
    [ -d "$d" ] && echo "  $(basename "$d")"
  done
}

# --- Parse args ---
if [ $# -eq 0 ] || [ "$1" = "-h" ] || [ "$1" = "--help" ]; then
  usage
  exit 0
fi

TARGET_NAME="$1"
shift

while [ $# -gt 0 ]; do
  case "$1" in
    -n) ITERATIONS="$2"; shift 2 ;;
    --model) MODEL="$2"; shift 2 ;;
    --no-branch) CREATE_BRANCH=false; shift ;;
    --no-baseline) RUN_BASELINE=false; shift ;;
    --dry-run) DRY_RUN=true; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage >&2; exit 1 ;;
  esac
done

TARGET_DIR="$EVALS_DIR/targets/$TARGET_NAME"
CONFIG_FILE="$TARGET_DIR/config.yaml"
RESULTS_FILE="$TARGET_DIR/results.tsv"

# --- Validate target ---
echo "=== Autoresearch: $TARGET_NAME ==="
echo ""

ERRORS=0

if [ ! -d "$TARGET_DIR" ]; then
  echo "ERROR: Target directory not found: $TARGET_DIR" >&2
  ERRORS=$((ERRORS + 1))
fi

if [ ! -f "$CONFIG_FILE" ]; then
  echo "ERROR: config.yaml not found" >&2
  ERRORS=$((ERRORS + 1))
fi

if [ ! -f "$TARGET_DIR/criteria.yaml" ]; then
  echo "ERROR: criteria.yaml not found" >&2
  ERRORS=$((ERRORS + 1))
fi

PROMPT_COUNT=0
for f in "$TARGET_DIR/prompts"/*.md; do
  [ -f "$f" ] && PROMPT_COUNT=$((PROMPT_COUNT + 1))
done
if [ "$PROMPT_COUNT" -eq 0 ]; then
  echo "ERROR: No prompt files in $TARGET_DIR/prompts/" >&2
  ERRORS=$((ERRORS + 1))
fi

if [ ! -f "$PROGRAM_MD" ]; then
  echo "ERROR: autoresearch-program.md not found" >&2
  ERRORS=$((ERRORS + 1))
fi

if ! command -v claude >/dev/null 2>&1; then
  echo "ERROR: claude CLI not found on PATH" >&2
  ERRORS=$((ERRORS + 1))
fi

if [ "$ERRORS" -gt 0 ]; then
  echo ""
  echo "$ERRORS error(s). Aborting." >&2
  exit 1
fi

# --- Read config ---
yaml_val() {
  grep "^${1}:" "$CONFIG_FILE" | head -1 | sed "s/^${1}: *//" | tr -d '"' | tr -d "'"
}

SKILL_NAME=$(yaml_val "name")
SKILL_MODEL=$(yaml_val "model")
JUDGE_MODEL=$(yaml_val "judge_model")
RUNS_PER=$(yaml_val "runs_per_iteration")
CRITERIA_COUNT=$(grep -c "^  - id:" "$TARGET_DIR/criteria.yaml" 2>/dev/null) || CRITERIA_COUNT=0

echo "Config:"
echo "  target:     $TARGET_NAME"
echo "  skill:      $SKILL_NAME"
echo "  model:      $SKILL_MODEL (eval) / $MODEL (loop agent)"
echo "  judge:      $JUDGE_MODEL"
echo "  prompts:    $PROMPT_COUNT"
echo "  criteria:   $CRITERIA_COUNT"
echo "  runs/iter:  $RUNS_PER"
echo "  iterations: ${ITERATIONS:-unlimited}"
echo ""

# --- Dry run exits here ---
if [ "$DRY_RUN" = true ]; then
  echo "Dry run — config is valid. Would launch Claude session with model=$MODEL."
  exit 0
fi

# --- Git branch ---
CURRENT_BRANCH=$(cd "$REPO_ROOT" && git branch --show-current 2>/dev/null || echo "")
DATE_SUFFIX=$(date +%b%d | tr '[:upper:]' '[:lower:]')
BRANCH_NAME="autoresearch/${TARGET_NAME}-${DATE_SUFFIX}"

if [ "$CREATE_BRANCH" = true ]; then
  case "$CURRENT_BRANCH" in
    autoresearch/*)
      echo "Already on autoresearch branch: $CURRENT_BRANCH"
      ;;
    *)
      if cd "$REPO_ROOT" && git show-ref --verify --quiet "refs/heads/$BRANCH_NAME" 2>/dev/null; then
        echo "Branch exists, checking out: $BRANCH_NAME"
        cd "$REPO_ROOT" && git checkout "$BRANCH_NAME"
      else
        echo "Creating branch: $BRANCH_NAME"
        cd "$REPO_ROOT" && git checkout -b "$BRANCH_NAME"
      fi
      ;;
  esac
  echo ""
fi

# --- Baseline ---
if [ "$RUN_BASELINE" = true ]; then
  HAS_KEEP=false
  if [ -f "$RESULTS_FILE" ]; then
    if grep -q "	keep	" "$RESULTS_FILE" 2>/dev/null; then
      HAS_KEEP=true
    fi
  fi

  if [ "$HAS_KEEP" = false ]; then
    echo "No baseline found. Running baseline eval..."
    echo ""
    "$EVALS_DIR/eval.sh" "$TARGET_NAME" --baseline
    echo ""
  else
    echo "Baseline exists. Skipping."
    echo ""
  fi
fi

# --- Build system prompt ---
SYSTEM_PROMPT=$(cat "$PROGRAM_MD")

if [ -n "$ITERATIONS" ]; then
  SYSTEM_PROMPT="$SYSTEM_PROMPT

## Iteration Limit

Stop after completing exactly $ITERATIONS iterations of the loop. After the final
iteration, print a summary: iterations run, kept count, discarded count, starting
score, ending best score. Then stop."
fi

# --- Session log ---
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
LOG_FILE="$TARGET_DIR/session-${TIMESTAMP}.log"

# --- Signal handler ---
cleanup() {
  echo ""
  echo "=== Autoresearch interrupted ==="
  echo ""
  "$EVALS_DIR/eval.sh" "$TARGET_NAME" --report 2>/dev/null || true
  echo ""
  echo "Session log: $LOG_FILE"
  echo "Dashboard:   ./evals/eval.sh $TARGET_NAME --dashboard"
  exit 0
}
trap cleanup SIGINT SIGTERM

# --- Launch ---
echo "Launching autonomous session..."
echo "  Model: $MODEL"
echo "  Log:   $LOG_FILE"
echo "  Stop:  Ctrl-C"
echo ""

INITIAL_PROMPT="Run autoresearch on $TARGET_NAME. Read evals/autoresearch-program.md for full instructions. Begin the optimization loop."

# Use script command to capture output while preserving interactivity
# Fall back to tee if script isn't available
if command -v script >/dev/null 2>&1; then
  script -q "$LOG_FILE" claude \
    --dangerously-skip-permissions \
    --model "$MODEL" \
    --system-prompt "$SYSTEM_PROMPT" \
    "$INITIAL_PROMPT"
else
  claude \
    --dangerously-skip-permissions \
    --model "$MODEL" \
    --system-prompt "$SYSTEM_PROMPT" \
    "$INITIAL_PROMPT" 2>&1 | tee "$LOG_FILE"
fi

# --- Post-run ---
echo ""
echo "=== Session complete ==="
echo ""
"$EVALS_DIR/eval.sh" "$TARGET_NAME" --report 2>/dev/null || true
echo ""
echo "Session log: $LOG_FILE"
echo "Dashboard:   ./evals/eval.sh $TARGET_NAME --dashboard"
