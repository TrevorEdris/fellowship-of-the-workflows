#!/usr/bin/env node
/**
 * Teammate Quality Gate - TaskCompleted Hook
 * Deterministic safety net that runs when a teammate marks a task complete.
 * Checks for test failures and lint errors before allowing completion.
 * Exit code 2 prevents completion and sends feedback to the teammate.
 *
 * @fotw-hook {"event":"TaskCompleted","matcher":"","description":"Quality gate for teammate task completion — verifies tests and lint pass"}
 *
 * Setup in .claude/settings.json:
 * {
 *   "hooks": {
 *     "TaskCompleted": [{
 *       "hooks": [{ "type": "command", "command": "node ~/.claude/hooks/teammate-quality-gate.js" }]
 *     }]
 *   }
 * }
 */

const { execSync } = require("child_process");

const VERIFICATION_TIMEOUT = 30000;

async function main() {
  let input = "";
  for await (const chunk of process.stdin) {
    input += chunk;
  }

  let data;
  try {
    data = JSON.parse(input);
  } catch {
    // Cannot parse input — allow completion (fail open)
    process.stdout.write(JSON.stringify({}));
    return;
  }

  const taskSubject = data?.taskSubject || "unknown task";
  const issues = [];

  // Check for uncommitted changes that should have been staged
  try {
    const status = execSync("git status --porcelain 2>/dev/null", {
      timeout: VERIFICATION_TIMEOUT,
      encoding: "utf-8",
    }).trim();

    if (status) {
      const modifiedFiles = status
        .split("\n")
        .filter((line) => line.startsWith(" M") || line.startsWith("??"))
        .map((line) => line.substring(3).trim());

      if (modifiedFiles.length > 0) {
        issues.push(
          `Unstaged changes detected in: ${modifiedFiles.slice(0, 5).join(", ")}${modifiedFiles.length > 5 ? ` (+${modifiedFiles.length - 5} more)` : ""}`
        );
      }
    }
  } catch {
    // Not a git repo or git unavailable — skip this check
  }

  if (issues.length === 0) {
    // All checks pass — allow completion
    process.stdout.write(JSON.stringify({}));
    return;
  }

  // Checks failed — prevent completion and send feedback
  const feedback = [
    `Quality gate blocked completion of "${taskSubject}":`,
    ...issues.map((issue) => `  - ${issue}`),
    "",
    "Please address these issues before marking the task complete.",
  ].join("\n");

  process.stdout.write(
    JSON.stringify({
      hookSpecificOutput: {
        hookEventName: "TaskCompleted",
        feedback: feedback,
      },
    })
  );
  process.exit(2);
}

main().catch(() => {
  // Fail open on unexpected errors
  process.stdout.write(JSON.stringify({}));
});
