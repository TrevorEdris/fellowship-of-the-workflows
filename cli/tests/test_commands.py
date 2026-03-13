"""Tests for CLI commands."""

import json
import os
import shutil
from pathlib import Path

import pytest
from typer.testing import CliRunner

from fotw.app import app

runner = CliRunner()


def test_list_all():
    result = runner.invoke(app, ["list"])
    assert result.exit_code == 0
    assert "Available Workflows" in result.output


def test_list_type_rule():
    result = runner.invoke(app, ["list", "--type", "rule"])
    assert result.exit_code == 0
    assert "rules" in result.output


def test_list_type_plural():
    """Plural forms should be accepted."""
    result = runner.invoke(app, ["list", "--type", "rules"])
    assert result.exit_code == 0


def test_list_type_invalid():
    result = runner.invoke(app, ["list", "--type", "bogus"])
    assert result.exit_code == 1
    assert "Unknown type" in result.output


def test_list_json():
    result = runner.invoke(app, ["list", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert isinstance(data, list)
    assert len(data) > 0


def test_list_json_type_filter():
    result = runner.invoke(app, ["list", "--json", "--type", "skill"])
    assert result.exit_code == 0
    assert "skill" in result.output


def test_validate():
    result = runner.invoke(app, ["validate"])
    assert result.exit_code == 0
    assert "Validation passed" in result.output


def test_validate_verbose():
    result = runner.invoke(app, ["validate", "--verbose"])
    assert result.exit_code == 0


def test_validate_quiet():
    result = runner.invoke(app, ["validate", "--quiet"])
    assert result.exit_code == 0
    assert "Validation passed" in result.output


# --- New command ---


@pytest.fixture
def isolated_workflows(tmp_path: Path, monkeypatch):
    """Set up an isolated repo root for new command tests.

    After the plugin-first flatten, WORKFLOWS_DIR == REPO_ROOT.
    Workflow dirs (rules/, skills/, agents/) live at repo root.
    """
    fake_root = tmp_path / "repo"
    (fake_root / "rules").mkdir(parents=True)
    (fake_root / "skills").mkdir(parents=True)
    (fake_root / "agents").mkdir(parents=True)
    monkeypatch.setenv("FOTW_REPO_ROOT", str(fake_root))
    # Force catalog module to re-resolve paths
    import fotw.services.catalog as catalog
    monkeypatch.setattr(catalog, "REPO_ROOT", fake_root)
    monkeypatch.setattr(catalog, "WORKFLOWS_DIR", fake_root)
    monkeypatch.setattr(catalog, "STARTERS_DIR", fake_root / "starters")
    # Also patch the imported reference in the new command module
    import fotw.commands.new as new_mod
    monkeypatch.setattr(new_mod, "WORKFLOWS_DIR", fake_root)
    return fake_root


def test_new_rule(isolated_workflows: Path):
    """Create a new rule."""
    result = runner.invoke(app, ["new", "rule/test-rule", "--yes", "--no-edit", "-d", "Test rule"])
    assert result.exit_code == 0
    target = isolated_workflows / "rules" / "test-rule.mdc"
    assert target.is_file()
    content = target.read_text()
    assert "description: Test rule" in content
    assert "globs:" in content


def test_new_skill(isolated_workflows: Path):
    """Create a new skill."""
    result = runner.invoke(app, ["new", "skill/test-skill", "--yes", "--no-edit", "-d", "Test skill"])
    assert result.exit_code == 0
    target_dir = isolated_workflows / "skills" / "test-skill"
    assert (target_dir / "SKILL.md").is_file()
    assert (target_dir / "scripts").is_dir()
    assert (target_dir / "references").is_dir()


def test_new_agent(isolated_workflows: Path):
    """Create a new agent."""
    result = runner.invoke(app, ["new", "agent/test-agent", "--yes", "--no-edit", "-d", "Test agent"])
    assert result.exit_code == 0
    target = isolated_workflows / "agents" / "test-agent.md"
    assert target.is_file()
    content = target.read_text()
    assert "description: Test agent" in content
    assert "tools:" in content


def test_new_invalid_type():
    """Invalid type should fail."""
    result = runner.invoke(app, ["new", "bogus/test", "--yes", "--no-edit"])
    assert result.exit_code == 1
    assert "Unknown type" in result.output


def test_new_invalid_path():
    """Missing slash should fail."""
    result = runner.invoke(app, ["new", "norule", "--yes", "--no-edit"])
    assert result.exit_code == 1
    assert "Invalid workflow path" in result.output


def test_new_duplicate_detection(isolated_workflows: Path):
    """Creating an existing workflow in non-interactive mode should error."""
    # Create first
    runner.invoke(app, ["new", "rule/dup-test", "--yes", "--no-edit", "-d", "First"])
    target = isolated_workflows / "rules" / "dup-test.mdc"
    assert target.is_file()
    # Try again without --yes (non-interactive, so exits with error)
    result = runner.invoke(app, ["new", "rule/dup-test", "--no-edit", "-d", "Second"])
    assert "already exists" in result.output
    assert result.exit_code == 1


def test_new_plural_type(isolated_workflows: Path):
    """Plural type should be normalized."""
    result = runner.invoke(app, ["new", "rules/plural-test", "--yes", "--no-edit", "-d", "Plural test"])
    assert result.exit_code == 0
    assert (isolated_workflows / "rules" / "plural-test.mdc").is_file()
