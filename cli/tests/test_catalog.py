"""Tests for catalog scanning."""

import pytest

from fotw.models.workflow import WorkflowType
from fotw.services.catalog import (
    VALID_MODELS,
    scan_agents,
    scan_all,
    scan_personas,
    scan_rules,
    scan_skills,
    validate_agent,
    validate_all,
)


def _write_agent(dir_path, model=None):
    """Write a minimal valid agent file, optionally with a model field."""
    lines = ["---", "name: probe-agent", "description: A probe agent for tests."]
    if model is not None:
        lines.append(f"model: {model}")
    lines += ["---", "", "Body."]
    path = dir_path / "probe-agent.md"
    path.write_text("\n".join(lines))
    return path


def test_scan_rules_returns_list():
    rules = scan_rules()
    assert isinstance(rules, list)
    assert len(rules) >= 2  # ai-session, discover-plan-implement
    names = [r.name for r in rules]
    assert "ai-session" in names
    assert "discover-plan-implement" in names


def test_scan_skills_returns_list():
    skills = scan_skills()
    assert isinstance(skills, list)
    assert len(skills) >= 1
    names = [s.name for s in skills]
    assert "code-review" in names


def test_scan_agents_returns_list():
    agents = scan_agents()
    assert isinstance(agents, list)
    assert len(agents) >= 1
    names = [a.name for a in agents]
    assert "pragmatic-code-review" in names


def test_scan_personas_returns_list():
    personas = scan_personas()
    assert isinstance(personas, list)
    assert len(personas) >= 1
    # Check that template is excluded
    names = [p.name for p in personas]
    assert "_template" not in names


def test_scan_all_returns_all_types():
    all_wf = scan_all()
    types = {wf.wtype.value for wf in all_wf}
    assert "rule" in types
    assert "skill" in types
    assert "agent" in types


def test_scan_rules_have_descriptions():
    rules = scan_rules()
    for rule in rules:
        assert rule.description, f"Rule {rule.name} has empty description"


def test_validate_all_no_errors():
    results = validate_all()
    errors = [r for r in results if not r.ok]
    assert len(errors) == 0, f"Validation errors: {errors}"


def test_validate_agent_warns_on_unknown_model(tmp_path):
    """An agent with a model outside the allowed set produces a warning."""
    path = _write_agent(tmp_path, model="fable")
    result = validate_agent(path)
    model_warnings = [w for w in result.warnings if "model" in w.lower()]
    assert model_warnings, f"Expected a model warning, got: {result.warnings}"
    assert "fable" in model_warnings[0]


@pytest.mark.parametrize("model", sorted(VALID_MODELS))
def test_validate_agent_accepts_known_models(tmp_path, model):
    """Every model in the allowed set passes without a model warning."""
    path = _write_agent(tmp_path, model=model)
    result = validate_agent(path)
    model_warnings = [w for w in result.warnings if "model" in w.lower()]
    assert not model_warnings, f"Unexpected model warning for '{model}': {model_warnings}"


def test_validate_agent_missing_model_ok(tmp_path):
    """An agent with no model field produces no model warning."""
    path = _write_agent(tmp_path, model=None)
    result = validate_agent(path)
    model_warnings = [w for w in result.warnings if "model" in w.lower()]
    assert not model_warnings, f"Unexpected model warning: {model_warnings}"


def test_inherit_is_a_valid_model():
    """`inherit` must be accepted so relay agents can defer to the session model."""
    assert "inherit" in VALID_MODELS


def test_workflow_type_from_str_singular():
    assert WorkflowType.from_str("rule") == WorkflowType.RULE
    assert WorkflowType.from_str("skill") == WorkflowType.SKILL
    assert WorkflowType.from_str("agent") == WorkflowType.AGENT


def test_workflow_type_from_str_plural():
    assert WorkflowType.from_str("rules") == WorkflowType.RULE
    assert WorkflowType.from_str("skills") == WorkflowType.SKILL
    assert WorkflowType.from_str("agents") == WorkflowType.AGENT
    assert WorkflowType.from_str("personas") == WorkflowType.PERSONA
