#!/usr/bin/env node
/**
 * Branch Guard - PreToolUse Hook for Edit|Write|Bash
 * Blocks file modifications and mutating git/shell commands on main/master.
 * Fails open: if not a git repo or git errors, allows the action.
 *
 * @fotw-hook {"event":"PreToolUse","matcher":"Edit|Write|Bash","description":"Blocks modifications on protected branches"}
 *
 * Setup in .claude/settings.json:
 * {
 *   "hooks": {
 *     "PreToolUse": [{
 *       "matcher": "Edit|Write|Bash",
 *       "hooks": [{ "type": "command", "command": "node ~/.claude/hooks/branch-guard.js" }]
 *     }]
 *   }
 * }
 */

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const PROTECTED_BRANCHES = ['main', 'master'];
const GIT_TIMEOUT = 3000;

// Paths that are always allowed regardless of branch
const ALLOWLIST = [
  new RegExp(`^${escapeRegex(path.join(process.env.HOME, '.claude'))}`),
  new RegExp(`^${escapeRegex(path.join(process.env.HOME, 'src', '.ai'))}`),
];

// Bash commands that mutate files or git state
const MUTATING_GIT_COMMANDS = [
  /\bgit\s+(commit|push|merge|rebase|cherry-pick|revert|reset|checkout\s+--)\b/,
  /\bgit\s+branch\s+-[dD]\b/,
];
const MUTATING_SHELL_COMMANDS = [
  /\bsed\s+-i\b/,
  /\btee\s+/,
  /[^<]>\s*\S/,    // redirect output to file (but not >>)
  /\bmv\s+/,
];

function escapeRegex(s) {
  return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

function findExistingAncestor(dir) {
  let d = dir;
  while (d && d !== path.dirname(d)) {
    try { if (fs.statSync(d).isDirectory()) return d; } catch {}
    d = path.dirname(d);
  }
  return null;
}

function getBranch(dir) {
  const existing = findExistingAncestor(dir);
  if (!existing) return null;
  try {
    const branch = execSync(`git -C "${existing}" rev-parse --abbrev-ref HEAD`, {
      timeout: GIT_TIMEOUT,
      stdio: ['pipe', 'pipe', 'pipe'],
    }).toString().trim();
    return branch;
  } catch {
    return null; // Not a git repo or git error — fail open
  }
}

function isProtected(branch) {
  return branch && PROTECTED_BRANCHES.includes(branch);
}

function isAllowlisted(filePath) {
  if (!filePath) return false;
  const resolved = path.resolve(filePath);
  return ALLOWLIST.some(re => re.test(resolved));
}

function isMutatingBashCommand(cmd) {
  if (!cmd) return false;
  for (const re of MUTATING_GIT_COMMANDS) {
    if (re.test(cmd)) return true;
  }
  for (const re of MUTATING_SHELL_COMMANDS) {
    if (re.test(cmd)) return true;
  }
  return false;
}

function check(toolName, toolInput, cwd) {
  if (!toolInput) return { blocked: false, reason: null };

  if (toolName === 'Edit' || toolName === 'Write') {
    const filePath = toolInput.file_path;
    if (!filePath) return { blocked: false, reason: null };
    if (isAllowlisted(filePath)) return { blocked: false, reason: null };

    const dir = path.dirname(path.resolve(filePath));
    const branch = getBranch(dir);
    if (!isProtected(branch)) return { blocked: false, reason: null };

    return {
      blocked: true,
      reason: `Cannot modify files on protected branch '${branch}'. Create a feature branch first.`,
    };
  }

  if (toolName === 'Bash') {
    const cmd = toolInput.command;
    if (!cmd) return { blocked: false, reason: null };
    if (!isMutatingBashCommand(cmd)) return { blocked: false, reason: null };

    const dir = cwd || process.cwd();
    const branch = getBranch(dir);
    if (!isProtected(branch)) return { blocked: false, reason: null };

    return {
      blocked: true,
      reason: `Cannot run mutating command on protected branch '${branch}'. Create a feature branch first.`,
    };
  }

  return { blocked: false, reason: null };
}

async function main() {
  let input = '';
  for await (const chunk of process.stdin) input += chunk;

  try {
    const data = JSON.parse(input);
    const { tool_name, tool_input, cwd } = data;

    if (!['Edit', 'Write', 'Bash'].includes(tool_name)) {
      return console.log('{}');
    }

    const result = check(tool_name, tool_input, cwd);

    if (result.blocked) {
      return console.log(JSON.stringify({
        hookSpecificOutput: {
          hookEventName: 'PreToolUse',
          permissionDecision: 'deny',
          permissionDecisionReason: `🛡️ [branch-guard] ${result.reason}`,
        },
      }));
    }
    console.log('{}');
  } catch (e) {
    console.log('{}'); // Fail open
  }
}

if (require.main === module) {
  main();
} else {
  module.exports = { check, getBranch, isProtected, isAllowlisted, isMutatingBashCommand };
}
