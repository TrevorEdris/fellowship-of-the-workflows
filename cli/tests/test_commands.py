"""Tests for CLI commands."""

import json

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
