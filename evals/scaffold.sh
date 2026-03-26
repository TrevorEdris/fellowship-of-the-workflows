#!/usr/bin/env bash
# Generate an eval target scaffold for a skill.
#
# Usage: ./evals/scaffold.sh <skill_name>
#
# Creates evals/targets/<skill_name>/ with config.yaml, criteria.yaml,
# judge-context.md, and a prompts/ directory. Uses Claude to analyze
# the skill's SKILL.md and golden tests to generate appropriate criteria
# and test prompts.
#
# You should review and edit the generated files before running evals.

set -euo pipefail

SKILL_NAME="${1:?Usage: scaffold.sh <skill_name>}"

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SKILL_DIR="$REPO_ROOT/skills/$SKILL_NAME"
SKILL_MD="$SKILL_DIR/SKILL.md"
TARGET_DIR="$REPO_ROOT/evals/targets/$SKILL_NAME"

if [[ ! -f "$SKILL_MD" ]]; then
  echo "ERROR: Skill not found: $SKILL_MD" >&2
  exit 1
fi

if [[ -d "$TARGET_DIR" ]]; then
  echo "ERROR: Target already exists: $TARGET_DIR" >&2
  echo "Delete it first if you want to regenerate." >&2
  exit 1
fi

mkdir -p "$TARGET_DIR/prompts"

# Read skill metadata
SKILL_CONTENT=$(cat "$SKILL_MD")
GOLDEN_FILE="$SKILL_DIR/tests/golden.jsonl"
GOLDEN_CONTENT=""
if [[ -f "$GOLDEN_FILE" ]]; then
  GOLDEN_CONTENT=$(cat "$GOLDEN_FILE")
fi

# Check for model in frontmatter
SKILL_MODEL=$(grep "^model:" "$SKILL_MD" 2>/dev/null | head -1 | sed 's/^model: *//' | tr -d '"' | tr -d "'" || echo "")
SKILL_MODEL="${SKILL_MODEL:-sonnet}"

# Check for agent
AGENT_NAME=$(grep "^agent:" "$SKILL_MD" 2>/dev/null | head -1 | sed 's/^agent: *//' | tr -d '"' | tr -d "'" || echo "")
READ_ONLY=""
if [[ -n "$AGENT_NAME" && -f "$REPO_ROOT/agents/$AGENT_NAME.md" ]]; then
  READ_ONLY="  - agents/$AGENT_NAME.md"
fi

# Collect reference files
REFS=$(find "$SKILL_DIR/references" -name "*.md" 2>/dev/null | while read -r f; do
  echo "  - ${f#$REPO_ROOT/}"
done)

# Generate config.yaml
cat > "$TARGET_DIR/config.yaml" <<EOF
name: $SKILL_NAME
type: skill
variable_files:
  - skills/$SKILL_NAME/SKILL.md
read_only_files:
${READ_ONLY:+$READ_ONLY}
${REFS}
runs_per_iteration: 3
model: $SKILL_MODEL
judge_model: sonnet
fallback_model: opus
EOF

echo "Created $TARGET_DIR/config.yaml"

# Use Claude to generate criteria and prompts
GENERATE_PROMPT="You are generating eval artifacts for an autoresearch system.

Given this skill definition:

---
$SKILL_CONTENT
---

$(if [[ -n "$GOLDEN_CONTENT" ]]; then echo "And these existing golden tests:"; echo '```jsonl'; echo "$GOLDEN_CONTENT"; echo '```'; fi)

Generate THREE outputs, separated by the marker '===SEPARATOR===':

OUTPUT 1: criteria.yaml
Generate 4-6 binary evaluation criteria in this YAML format:
\`\`\`yaml
criteria:
  - id: snake_case_id
    question: \"Yes/no question the judge can answer about the skill's output\"
\`\`\`
Criteria should cover: recall (did it find issues?), precision (did it avoid false positives?), output quality (actionable, specific?), and format (structured output?).

===SEPARATOR===

OUTPUT 2: judge-context.md
Generate a judge context file with ground truth for each test prompt you'll create. Format:
# <Skill Name> Judge Context
## Ground Truth Per Prompt
### Prompt 01 (<slug>): <description>
**REAL ISSUES:** ...
**NOT ISSUES:** ...

===SEPARATOR===

OUTPUT 3: Test prompts
Generate 3-5 test prompts, each separated by '---PROMPT---' with a filename on the first line.
Each prompt should be a realistic input that exercises the skill.
Include at least one 'clean' input with no issues (false positive test).

Do NOT include any explanation outside these three outputs."

echo "Generating criteria, judge context, and prompts via Claude..."

GENERATED=$(claude -p \
  --model sonnet \
  --bare \
  --dangerously-skip-permissions \
  --output-format text \
  "$GENERATE_PROMPT" 2>/dev/null)

if [[ -z "$GENERATED" ]]; then
  echo "ERROR: Claude returned empty output. Creating empty scaffolds instead." >&2
  cat > "$TARGET_DIR/criteria.yaml" <<'EOF'
criteria:
  - id: placeholder
    question: "TODO: Add criteria"
EOF
  echo "# Judge Context\n\nTODO: Add ground truth" > "$TARGET_DIR/judge-context.md"
  echo "TODO: Add test prompt" > "$TARGET_DIR/prompts/01-placeholder.md"
  echo ""
  echo "Scaffold created at $TARGET_DIR — fill in manually."
  exit 0
fi

# Parse the three sections
CRITERIA_SECTION=$(echo "$GENERATED" | sed -n '1,/===SEPARATOR===/p' | head -n -1)
JUDGE_SECTION=$(echo "$GENERATED" | sed -n '/===SEPARATOR===/,/===SEPARATOR===/p' | tail -n +2 | head -n -1)
PROMPTS_SECTION=$(echo "$GENERATED" | sed -n '/===SEPARATOR===/,$p' | tail -n +2)

# Extract YAML from criteria (strip markdown code fences if present)
echo "$CRITERIA_SECTION" | sed '/^```/d' > "$TARGET_DIR/criteria.yaml"
echo "Created $TARGET_DIR/criteria.yaml"

echo "$JUDGE_SECTION" > "$TARGET_DIR/judge-context.md"
echo "Created $TARGET_DIR/judge-context.md"

# Split prompts
PROMPT_NUM=1
echo "$PROMPTS_SECTION" | while IFS= read -r line; do
  if [[ "$line" == "---PROMPT---" ]]; then
    PROMPT_NUM=$((PROMPT_NUM + 1))
    continue
  fi
  PROMPT_FILE="$TARGET_DIR/prompts/$(printf '%02d' $PROMPT_NUM)-generated.md"
  echo "$line" >> "$PROMPT_FILE"
done
echo "Created prompt files in $TARGET_DIR/prompts/"

echo ""
echo "Target scaffold generated at $TARGET_DIR"
echo "REVIEW AND EDIT before running evals — generated content needs human validation."
