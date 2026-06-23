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
  let personaContext, tmpProject;

  beforeEach(() => {
    ({ personaContext } = tryRequire());
    tmpProject = fs.mkdtempSync(path.join(os.tmpdir(), 'pc-test-'));
    fs.mkdirSync(path.join(tmpProject, '.claude'), { recursive: true });
  });

  afterEach(() => {
    try { fs.rmSync(tmpProject, { recursive: true, force: true }); } catch {}
  });

  function writeConfig(content) {
    fs.writeFileSync(path.join(tmpProject, '.claude', 'persona.yaml'), content);
  }

  it('injects persona and intensity from persona.yaml', () => {
    writeConfig('persona: rocky\nintensity: excessive\n');
    const result = personaContext(tmpProject);
    assert.equal(result.inject, true);
    assert.match(result.message, /Active persona: rocky, intensity: excessive/);
  });

  it('defaults intensity to noticeable when missing', () => {
    writeConfig('persona: gandalf\n');
    const result = personaContext(tmpProject);
    assert.equal(result.inject, true);
    assert.match(result.message, /intensity: noticeable/);
  });

  it('stays silent when no config exists', () => {
    const result = personaContext(tmpProject);
    assert.equal(result.inject, false);
  });

  it('stays silent when persona is off', () => {
    writeConfig('persona: off\n');
    assert.equal(personaContext(tmpProject).inject, false);
  });

  it('stays silent when intensity is off', () => {
    writeConfig('persona: gandalf\nintensity: off\n');
    assert.equal(personaContext(tmpProject).inject, false);
  });

  it('ignores comments and quoting in values', () => {
    writeConfig('persona: "spock"  # logical\nintensity: minimal\n');
    const result = personaContext(tmpProject);
    assert.match(result.message, /Active persona: spock, intensity: minimal/);
  });

  it('ignores the previous-value record keys', () => {
    writeConfig(
      'persona: rocky\nintensity: noticeable\nprevious-output-style: Explanatory\nprevious-spinner-verbs: null\n'
    );
    const result = personaContext(tmpProject);
    assert.equal(result.inject, true);
    assert.match(result.message, /Active persona: rocky/);
  });
});
