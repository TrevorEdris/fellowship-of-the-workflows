"""Tests for the setup command."""

import json
from pathlib import Path

import pytest

from fotw.models.lock import LOCK_FILENAME, LockEntry, read_lock
from fotw.services.catalog import WORKFLOWS_DIR, scan_rules


@pytest.fixture
def tmp_target(tmp_path: Path) -> Path:
    """Create a temporary target directory."""
    target = tmp_path / "test-project"
    target.mkdir()
    return target


def _run_setup(tmp_target: Path, tool: str = "claude-code", force: bool = True, dry_run: bool = False):
    """Helper to invoke setup_cmd programmatically."""
    from fotw.commands.setup import setup_cmd
    from unittest.mock import patch

    # Typer commands raise SystemExit on typer.Exit — catch it
    try:
        setup_cmd(
            target_repo=str(tmp_target),
            for_tool=tool,
            force=force,
            dry_run=dry_run,
            rules_only=True,
        )
    except SystemExit:
        pass


def test_setup_creates_lock_file(tmp_target: Path):
    """Setup creates a .fotw-lock.json in the project root."""
    _run_setup(tmp_target)
    lock_path = tmp_target / LOCK_FILENAME
    assert lock_path.is_file()


def test_setup_lock_has_entries(tmp_target: Path):
    """Lock file contains one entry per installed rule."""
    _run_setup(tmp_target)
    entries = read_lock(tmp_target)
    rules = scan_rules()
    assert len(entries) == len(rules)


def test_setup_lock_entry_fields(tmp_target: Path):
    """Each lock entry has the expected fields."""
    _run_setup(tmp_target)
    entries = read_lock(tmp_target)
    assert len(entries) > 0
    entry = entries[0]
    assert entry.workflow_id.startswith("rules/")
    assert entry.tool == "claude-code"
    assert entry.target_path.startswith(".claude/rules/")
    assert len(entry.source_hash) == 64  # SHA256 hex
    assert "T" in entry.installed_at  # ISO 8601


def test_setup_installs_rules(tmp_target: Path):
    """Setup actually installs rule files to the target."""
    _run_setup(tmp_target)
    rules_dir = tmp_target / ".claude" / "rules"
    assert rules_dir.is_dir()
    installed = list(rules_dir.glob("*.md"))
    rules = scan_rules()
    assert len(installed) == len(rules)


def test_setup_cursor(tmp_target: Path):
    """Setup for cursor installs .mdc files."""
    _run_setup(tmp_target, tool="cursor")
    rules_dir = tmp_target / ".cursor" / "rules"
    assert rules_dir.is_dir()
    installed = list(rules_dir.glob("*.mdc"))
    assert len(installed) > 0
    entries = read_lock(tmp_target)
    assert all(e.tool == "cursor" for e in entries)


def test_setup_dry_run_no_files(tmp_target: Path):
    """Dry run creates no files."""
    _run_setup(tmp_target, dry_run=True)
    assert not (tmp_target / LOCK_FILENAME).exists()
    assert not (tmp_target / ".claude" / "rules").exists()


def test_setup_lock_valid_json(tmp_target: Path):
    """Lock file is valid JSON with expected structure."""
    _run_setup(tmp_target)
    lock_path = tmp_target / LOCK_FILENAME
    data = json.loads(lock_path.read_text())
    assert "version" in data
    assert data["version"] == 1
    assert "entries" in data
    assert isinstance(data["entries"], list)


def test_setup_idempotent(tmp_target: Path):
    """Running setup twice produces the same number of lock entries."""
    _run_setup(tmp_target)
    entries1 = read_lock(tmp_target)
    _run_setup(tmp_target)
    entries2 = read_lock(tmp_target)
    assert len(entries1) == len(entries2)
