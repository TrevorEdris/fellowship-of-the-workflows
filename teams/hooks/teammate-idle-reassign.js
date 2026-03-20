#!/usr/bin/env node
/**
 * Teammate Idle Reassign - TeammateIdle Hook
 * Runs when a teammate finishes and is about to go idle.
 * Checks the shared task list for unclaimed pending tasks.
 * Exit code 2 sends feedback telling the teammate to claim the next task.
 *
 * @fotw-hook {"event":"TeammateIdle","matcher":"","description":"Reassigns idle teammates to unclaimed tasks"}
 *
 * Setup in .claude/settings.json:
 * {
 *   "hooks": {
 *     "TeammateIdle": [{
 *       "hooks": [{ "type": "command", "command": "node ~/.claude/hooks/teammate-idle-reassign.js" }]
 *     }]
 *   }
 * }
 */

async function main() {
  let input = "";
  for await (const chunk of process.stdin) {
    input += chunk;
  }

  let data;
  try {
    data = JSON.parse(input);
  } catch {
    // Cannot parse input — allow idle (fail open)
    process.stdout.write(JSON.stringify({}));
    return;
  }

  const pendingTasks = data?.pendingTasks || [];
  const teammateName = data?.teammateName || "teammate";

  if (pendingTasks.length === 0) {
    // No unclaimed tasks — allow idle
    process.stdout.write(JSON.stringify({}));
    return;
  }

  // There are unclaimed tasks — tell the teammate to pick one up
  const nextTask = pendingTasks[0];
  const feedback = [
    `There are ${pendingTasks.length} unclaimed task(s) remaining.`,
    `Next available: "${nextTask.subject || nextTask.title || "untitled"}"`,
    "",
    "Please claim and work on this task before going idle.",
  ].join("\n");

  process.stdout.write(
    JSON.stringify({
      hookSpecificOutput: {
        hookEventName: "TeammateIdle",
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
