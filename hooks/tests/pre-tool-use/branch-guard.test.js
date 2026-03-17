const { describe, it, beforeEach, afterEach, mock } = require('node:test');
const assert = require('node:assert/strict');
const path = require('node:path');
const fs = require('node:fs');
const os = require('node:os');
const { execSync } = require('node:child_process');

// We'll require the module under test after it exists
let branchGuard;

function tryRequire() {
  // Clear cache so each test gets fresh module
  const modPath = path.resolve(__dirname, '../../branch-guard.js');
  delete require.cache[modPath];
  return require(modPath);
}

// Helper: create a temp git repo on a given branch
function makeTempRepo(branch = 'main') {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'bg-test-'));
  execSync('git init', { cwd: dir, stdio: 'ignore' });
  execSync('git checkout -b ' + branch, { cwd: dir, stdio: 'ignore' });
  // Need at least one commit for branch to exist
  fs.writeFileSync(path.join(dir, 'dummy.txt'), 'x');
  execSync('git add . && git commit -m "init"', { cwd: dir, stdio: 'ignore' });
  return dir;
}

function cleanup(dir) {
  try { fs.rmSync(dir, { recursive: true, force: true }); } catch {}
}

describe('branch-guard', () => {
  let mainRepo, featureRepo, nonGitDir;

  beforeEach(() => {
    branchGuard = tryRequire();
    mainRepo = makeTempRepo('main');
    featureRepo = makeTempRepo('feature/test');
    nonGitDir = fs.mkdtempSync(path.join(os.tmpdir(), 'bg-nogit-'));
  });

  afterEach(() => {
    cleanup(mainRepo);
    cleanup(featureRepo);
    cleanup(nonGitDir);
  });

  // --- Edit/Write tool tests ---

  describe('Edit/Write on protected branch', () => {
    it('blocks Edit to a file in a repo on main', () => {
      const filePath = path.join(mainRepo, 'src/app.js');
      const result = branchGuard.check('Edit', { file_path: filePath });
      assert.equal(result.blocked, true);
      assert.match(result.reason, /main|master|protected/i);
    });

    it('blocks Write to a file in a repo on master', () => {
      const masterRepo = makeTempRepo('master');
      try {
        const filePath = path.join(masterRepo, 'index.js');
        const result = branchGuard.check('Write', { file_path: filePath });
        assert.equal(result.blocked, true);
      } finally {
        cleanup(masterRepo);
      }
    });

    it('allows Edit to a file in a repo on feature branch', () => {
      const filePath = path.join(featureRepo, 'src/app.js');
      const result = branchGuard.check('Edit', { file_path: filePath });
      assert.equal(result.blocked, false);
    });
  });

  // --- Allowlist tests ---

  describe('allowlist', () => {
    it('allows Edit to ~/.claude/* even if somehow on main', () => {
      const filePath = path.join(process.env.HOME, '.claude', 'hooks', 'test.js');
      const result = branchGuard.check('Edit', { file_path: filePath });
      assert.equal(result.blocked, false);
    });

    it('allows Write to ~/src/.ai/* even if on main', () => {
      const filePath = path.join(process.env.HOME, 'src', '.ai', 'sessions', 'test', 'SESSION.md');
      const result = branchGuard.check('Write', { file_path: filePath });
      assert.equal(result.blocked, false);
    });

    it('allows Edit to files not in a git repo (fails open)', () => {
      const filePath = path.join(nonGitDir, 'random.txt');
      const result = branchGuard.check('Edit', { file_path: filePath });
      assert.equal(result.blocked, false);
    });
  });

  // --- Bash tool tests ---

  describe('Bash commands on protected branch', () => {
    it('blocks git commit when cwd is on main', () => {
      const result = branchGuard.check('Bash', { command: 'git commit -m "oops"' }, mainRepo);
      assert.equal(result.blocked, true);
    });

    it('blocks git push when cwd is on main', () => {
      const result = branchGuard.check('Bash', { command: 'git push origin main' }, mainRepo);
      assert.equal(result.blocked, true);
    });

    it('allows git commit on a feature branch', () => {
      const result = branchGuard.check('Bash', { command: 'git commit -m "ok"' }, featureRepo);
      assert.equal(result.blocked, false);
    });

    it('allows git status on main (read-only)', () => {
      const result = branchGuard.check('Bash', { command: 'git status' }, mainRepo);
      assert.equal(result.blocked, false);
    });

    it('allows git log on main (read-only)', () => {
      const result = branchGuard.check('Bash', { command: 'git log --oneline' }, mainRepo);
      assert.equal(result.blocked, false);
    });

    it('allows git diff on main (read-only)', () => {
      const result = branchGuard.check('Bash', { command: 'git diff HEAD~1' }, mainRepo);
      assert.equal(result.blocked, false);
    });

    it('blocks sed -i when cwd is on main', () => {
      const result = branchGuard.check('Bash', { command: 'sed -i "" "s/old/new/g" file.txt' }, mainRepo);
      assert.equal(result.blocked, true);
    });

    it('blocks tee (file write) when cwd is on main', () => {
      const result = branchGuard.check('Bash', { command: 'echo "x" | tee file.txt' }, mainRepo);
      assert.equal(result.blocked, true);
    });

    it('blocks redirect > when cwd is on main', () => {
      const result = branchGuard.check('Bash', { command: 'echo "x" > file.txt' }, mainRepo);
      assert.equal(result.blocked, true);
    });

    it('allows non-git, non-file-modifying commands on main', () => {
      const result = branchGuard.check('Bash', { command: 'ls -la' }, mainRepo);
      assert.equal(result.blocked, false);
    });

    it('allows Bash in non-git directory (fails open)', () => {
      const result = branchGuard.check('Bash', { command: 'git commit -m "no repo"' }, nonGitDir);
      assert.equal(result.blocked, false);
    });
  });

  // --- Edge cases ---

  describe('edge cases', () => {
    it('handles missing file_path gracefully', () => {
      const result = branchGuard.check('Edit', {});
      assert.equal(result.blocked, false);
    });

    it('handles missing tool_input gracefully', () => {
      const result = branchGuard.check('Edit', null);
      assert.equal(result.blocked, false);
    });

    it('ignores non-matched tools', () => {
      const result = branchGuard.check('Read', { file_path: path.join(mainRepo, 'x.js') });
      assert.equal(result.blocked, false);
    });
  });
});
