const { describe, it, beforeEach, afterEach } = require('node:test');
const assert = require('node:assert/strict');
const path = require('node:path');
const fs = require('node:fs');
const os = require('node:os');

let sessionReminder;

function tryRequire() {
  const modPath = path.resolve(__dirname, '../../session-reminder.js');
  delete require.cache[modPath];
  return require(modPath);
}

function todayPrefix() {
  return new Date().toISOString().slice(0, 10); // YYYY-MM-DD
}

describe('session-reminder', () => {
  let tmpSessionRoot;

  beforeEach(() => {
    sessionReminder = tryRequire();
    tmpSessionRoot = fs.mkdtempSync(path.join(os.tmpdir(), 'sr-test-'));
  });

  afterEach(() => {
    try { fs.rmSync(tmpSessionRoot, { recursive: true, force: true }); } catch {}
  });

  it('returns reminder when no session dir exists for today', () => {
    const result = sessionReminder.checkSession(tmpSessionRoot);
    assert.ok(result.remind, 'should remind when no session dir exists');
    assert.ok(result.message.length > 0, 'message should not be empty');
  });

  it('returns no reminder when a session dir exists for today', () => {
    const dir = path.join(tmpSessionRoot, `${todayPrefix()}_TEST-123_Some-Task`);
    fs.mkdirSync(dir, { recursive: true });
    const result = sessionReminder.checkSession(tmpSessionRoot);
    assert.equal(result.remind, false);
  });

  it('ignores session dirs from other dates', () => {
    const dir = path.join(tmpSessionRoot, '1999-01-01_OLD_Task');
    fs.mkdirSync(dir, { recursive: true });
    const result = sessionReminder.checkSession(tmpSessionRoot);
    assert.ok(result.remind, 'should remind — only old session dirs exist');
  });

  it('handles missing session root gracefully', () => {
    const result = sessionReminder.checkSession('/tmp/nonexistent-sr-test-dir');
    assert.ok(result.remind, 'should remind when session root does not exist');
  });

  it('returns proper hook output structure when reminding', () => {
    const result = sessionReminder.checkSession(tmpSessionRoot);
    assert.ok(result.remind);
    // Verify the message mentions creating a session directory
    assert.match(result.message, /session/i);
  });
});
