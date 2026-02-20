"""Tests for catalog scanning."""

from fotw.models.workflow import WorkflowType
from fotw.services.catalog import (
    scan_agents,
    scan_all,
    scan_personas,
    scan_rules,
    scan_skills,
    scan_starters,
    validate_all,
)


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


def test_scan_starters_returns_list():
    starters = scan_starters()
    assert isinstance(starters, list)
    assert len(starters) == 3
    tiers = [s.tier for s in starters]
    assert "minimal" in tiers
    assert "standard" in tiers
    assert "full" in tiers


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


def test_workflow_type_from_str_singular():
    assert WorkflowType.from_str("rule") == WorkflowType.RULE
    assert WorkflowType.from_str("skill") == WorkflowType.SKILL
    assert WorkflowType.from_str("agent") == WorkflowType.AGENT


def test_workflow_type_from_str_plural():
    assert WorkflowType.from_str("rules") == WorkflowType.RULE
    assert WorkflowType.from_str("skills") == WorkflowType.SKILL
    assert WorkflowType.from_str("agents") == WorkflowType.AGENT
    assert WorkflowType.from_str("starters") == WorkflowType.STARTER
    assert WorkflowType.from_str("personas") == WorkflowType.PERSONA
