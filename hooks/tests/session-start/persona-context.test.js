const { describe, it, beforeEach, afterEach } = require('node:test');
const assert = require('node:assert/strict');
const path = require('node:path');
const fs = require('node:fs');
const os = require('node:os');

function tryRequire() {
  const modPath = path.resolve(__dirname, '../../persona-context.js');
  delete require.cache[modPath];
  return require(modPath);
}

describe('persona-context', () => {
  let personaContext, tmpProject, tmpHome;

  beforeEach(() => {
    ({ personaContext } = tryRequire());
    tmpProject = fs.mkdtempSync(path.join(os.tmpdir(), 'pc-test-'));
    fs.mkdirSync(path.join(tmpProject, '.claude'), { recursive: true });
    // Isolated, empty home so the global fallback never reads the real
    // ~/.claude/persona.yaml during tests.
    tmpHome = fs.mkdtempSync(path.join(os.tmpdir(), 'pc-home-'));
    fs.mkdirSync(path.join(tmpHome, '.claude'), { recursive: true });
  });

  afterEach(() => {
    try { fs.rmSync(tmpProject, { recursive: true, force: true }); } catch {}
    try { fs.rmSync(tmpHome, { recursive: true, force: true }); } catch {}
  });

  function writeConfig(content) {
    fs.writeFileSync(path.join(tmpProject, '.claude', 'persona.yaml'), content);
  }

  function writeHomeConfig(content) {
    fs.writeFileSync(path.join(tmpHome, '.claude', 'persona.yaml'), content);
  }

  it('injects persona and intensity from persona.yaml', () => {
    writeConfig('persona: rocky\nintensity: excessive\n');
    const result = personaContext(tmpProject, tmpHome);
    assert.equal(result.inject, true);
    assert.match(result.message, /Active persona: rocky, intensity: excessive/);
  });

  it('defaults intensity to noticeable when missing', () => {
    writeConfig('persona: gandalf\n');
    const result = personaContext(tmpProject, tmpHome);
    assert.equal(result.inject, true);
    assert.match(result.message, /intensity: noticeable/);
  });

  it('stays silent when no config exists', () => {
    const result = personaContext(tmpProject, tmpHome);
    assert.equal(result.inject, false);
  });

  it('stays silent when persona is off', () => {
    writeConfig('persona: off\n');
    assert.equal(personaContext(tmpProject, tmpHome).inject, false);
  });

  it('stays silent when intensity is off', () => {
    writeConfig('persona: gandalf\nintensity: off\n');
    assert.equal(personaContext(tmpProject, tmpHome).inject, false);
  });

  it('ignores comments and quoting in values', () => {
    writeConfig('persona: "spock"  # logical\nintensity: minimal\n');
    const result = personaContext(tmpProject, tmpHome);
    assert.match(result.message, /Active persona: spock, intensity: minimal/);
  });

  it('ignores the previous-value record keys', () => {
    writeConfig(
      'persona: rocky\nintensity: noticeable\nprevious-output-style: Explanatory\nprevious-spinner-verbs: null\n'
    );
    const result = personaContext(tmpProject, tmpHome);
    assert.equal(result.inject, true);
    assert.match(result.message, /Active persona: rocky/);
  });

  it('falls back to the global ~/.claude config when no project config exists', () => {
    writeHomeConfig('persona: picard\nintensity: noticeable\n');
    const result = personaContext(tmpProject, tmpHome);
    assert.equal(result.inject, true);
    assert.match(result.message, /Active persona: picard/);
  });

  it('prefers the project config over the global config', () => {
    writeConfig('persona: rocky\nintensity: minimal\n');
    writeHomeConfig('persona: picard\nintensity: excessive\n');
    const result = personaContext(tmpProject, tmpHome);
    assert.match(result.message, /Active persona: rocky, intensity: minimal/);
  });
});
