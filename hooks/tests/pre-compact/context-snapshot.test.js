const { describe, it, beforeEach, afterEach } = require('node:test');
const assert = require('node:assert/strict');
const path = require('node:path');
const fs = require('node:fs');
const os = require('node:os');

let contextSnapshot;

function tryRequire() {
  const modPath = path.resolve(__dirname, '../../context-snapshot.js');
  delete require.cache[modPath];
  return require(modPath);
}

function todayPrefix() {
  return new Date().toISOString().slice(0, 10);
}

describe('context-snapshot', () => {
  let tmpSessionRoot, sessionDir;

  beforeEach(() => {
    contextSnapshot = tryRequire();
    tmpSessionRoot = fs.mkdtempSync(path.join(os.tmpdir(), 'cs-test-'));
    sessionDir = path.join(tmpSessionRoot, `${todayPrefix()}_TEST-1_Snapshot-Test`);
    fs.mkdirSync(sessionDir, { recursive: true });
  });

  afterEach(() => {
    try { fs.rmSync(tmpSessionRoot, { recursive: true, force: true }); } catch {}
  });

  // --- Phase inference ---

  describe('phase inference', () => {
    it('infers "discover" when only SESSION.md exists', () => {
      fs.writeFileSync(path.join(sessionDir, 'SESSION.md'), '# Session\n## Log\n- did stuff');
      const result = contextSnapshot.createSnapshot(tmpSessionRoot);
      assert.equal(result.phase, 'discover');
    });

    it('infers "plan" when SESSION.md + DISCOVERY.md exist', () => {
      fs.writeFileSync(path.join(sessionDir, 'SESSION.md'), '# Session');
      fs.writeFileSync(path.join(sessionDir, 'DISCOVERY.md'), '# Discovery\n## Findings');
      const result = contextSnapshot.createSnapshot(tmpSessionRoot);
      assert.equal(result.phase, 'plan');
    });

    it('infers "implement" when SESSION.md + DISCOVERY.md + PLAN.md exist', () => {
      fs.writeFileSync(path.join(sessionDir, 'SESSION.md'), '# Session');
      fs.writeFileSync(path.join(sessionDir, 'DISCOVERY.md'), '# Discovery');
      fs.writeFileSync(path.join(sessionDir, 'PLAN.md'), '# Plan\n## Steps\n1. Do thing');
      const result = contextSnapshot.createSnapshot(tmpSessionRoot);
      assert.equal(result.phase, 'implement');
    });
  });

  // --- Snapshot file creation ---

  describe('snapshot output', () => {
    it('writes CONTEXT_SNAPSHOT.md to session dir', () => {
      fs.writeFileSync(path.join(sessionDir, 'SESSION.md'), '# Session\n- entry');
      contextSnapshot.createSnapshot(tmpSessionRoot);
      const snapshotPath = path.join(sessionDir, 'CONTEXT_SNAPSHOT.md');
      assert.ok(fs.existsSync(snapshotPath), 'CONTEXT_SNAPSHOT.md should exist');
    });

    it('includes timestamp in snapshot', () => {
      fs.writeFileSync(path.join(sessionDir, 'SESSION.md'), '# Session');
      contextSnapshot.createSnapshot(tmpSessionRoot);
      const content = fs.readFileSync(path.join(sessionDir, 'CONTEXT_SNAPSHOT.md'), 'utf8');
      // Should contain an ISO-ish timestamp
      assert.match(content, /\d{4}-\d{2}-\d{2}/);
    });

    it('includes phase in snapshot', () => {
      fs.writeFileSync(path.join(sessionDir, 'SESSION.md'), '# Session');
      fs.writeFileSync(path.join(sessionDir, 'PLAN.md'), '# Plan');
      contextSnapshot.createSnapshot(tmpSessionRoot);
      const content = fs.readFileSync(path.join(sessionDir, 'CONTEXT_SNAPSHOT.md'), 'utf8');
      assert.match(content, /implement/i);
    });
  });

  // --- Heading extraction ---

  describe('heading extraction', () => {
    it('extracts h2 headings from markdown files', () => {
      fs.writeFileSync(path.join(sessionDir, 'SESSION.md'), '# Session\n## Log\nstuff\n## Questions\nq1');
      fs.writeFileSync(path.join(sessionDir, 'PLAN.md'), '# Plan\n## Steps\n1. foo\n## Risks\nbar');
      const result = contextSnapshot.createSnapshot(tmpSessionRoot);
      assert.ok(result.snapshot.includes('Log'), 'should extract Log heading');
      assert.ok(result.snapshot.includes('Steps'), 'should extract Steps heading');
      assert.ok(result.snapshot.includes('Risks'), 'should extract Risks heading');
    });
  });

  // --- Edge cases ---

  describe('edge cases', () => {
    it('returns empty result when no session dir exists for today', () => {
      const emptyRoot = fs.mkdtempSync(path.join(os.tmpdir(), 'cs-empty-'));
      try {
        const result = contextSnapshot.createSnapshot(emptyRoot);
        assert.equal(result.phase, null);
        assert.equal(result.snapshot, null);
      } finally {
        fs.rmSync(emptyRoot, { recursive: true, force: true });
      }
    });

    it('returns empty result when session root does not exist', () => {
      const result = contextSnapshot.createSnapshot('/tmp/nonexistent-cs-test-dir');
      assert.equal(result.phase, null);
    });

    it('picks most recently named session dir if multiple exist for today', () => {
      const dir2 = path.join(tmpSessionRoot, `${todayPrefix()}_TEST-2_Later-Task`);
      fs.mkdirSync(dir2, { recursive: true });
      fs.writeFileSync(path.join(dir2, 'SESSION.md'), '# Session 2');
      fs.writeFileSync(path.join(dir2, 'DISCOVERY.md'), '# Discovery 2');
      // sessionDir (TEST-1) has no files — dir2 (TEST-2) has SESSION + DISCOVERY
      const result = contextSnapshot.createSnapshot(tmpSessionRoot);
      // Should use TEST-2 (sorts later alphabetically)
      assert.equal(result.phase, 'plan');
    });
  });
});
