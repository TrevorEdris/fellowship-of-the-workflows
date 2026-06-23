"""Tests for the update command."""

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from fotw.models.lock import (
    LOCK_FILENAME,
    LockEntry,
    compute_source_hash,
    read_lock,
    write_lock,
)
from fotw.services.catalog import WORKFLOWS_DIR, scan_rules


@pytest.fixture
def tmp_target(tmp_path: Path) -> Path:
    """Create a temporary target directory."""
    target = tmp_path / "test-project"
    target.mkdir()
    return target


def _run_setup(tmp_target: Path, tool: str = "claude-code"):
    """Helper to invoke setup_cmd."""
    from fotw.commands.setup import setup_cmd

    try:
        setup_cmd(
            target_repo=str(tmp_target),
            for_tool=tool,
            force=True,
            dry_run=False,
            rules_only=True,
        )
    except SystemExit:
        pass


def _run_update(tmp_target: Path, force: bool = False, dry_run: bool = False):
    """Helper to invoke update_cmd."""
    from fotw.commands.update import update_cmd

    try:
        update_cmd(
            target_repo=str(tmp_target),
            force=force,
            dry_run=dry_run,
        )
    except SystemExit:
        pass


def test_update_no_lock_exits(tmp_target: Path):
    """Update without a lock file exits with error."""
    import typer

    from fotw.commands.update import update_cmd

    # typer.Exit is the public exit exception; recent typer versions vendor
    # click as typer._click, so catching standalone click.exceptions.Exit no
    # longer matches what the command raises.
    with pytest.raises((SystemExit, typer.Exit)):
        update_cmd(target_repo=str(tmp_target), force=False, dry_run=False)


def test_update_unchanged_skips(tmp_target: Path):
    """Update with unchanged sources keeps the same hashes."""
    _run_setup(tmp_target)
    entries_before = read_lock(tmp_target)
    _run_update(tmp_target)
    entries_after = read_lock(tmp_target)
    # Hashes should be unchanged
    hashes_before = {e.workflow_id: e.source_hash for e in entries_before}
    hashes_after = {e.workflow_id: e.source_hash for e in entries_after}
    assert hashes_before == hashes_after


def test_update_force_reinstalls(tmp_target: Path):
    """Update with --force re-installs even with same hashes."""
    _run_setup(tmp_target)
    entries_before = read_lock(tmp_target)
    _run_update(tmp_target, force=True)
    entries_after = read_lock(tmp_target)
    # All entries should have updated timestamps
    for before, after in zip(
        sorted(entries_before, key=lambda e: e.workflow_id),
        sorted(entries_after, key=lambda e: e.workflow_id),
    ):
        assert before.workflow_id == after.workflow_id
        # Force update changes installed_at
        assert after.installed_at >= before.installed_at


def test_update_dry_run_no_change(tmp_target: Path):
    """Update with --dry-run doesn't modify lock file."""
    _run_setup(tmp_target)
    lock_path = tmp_target / LOCK_FILENAME
    content_before = lock_path.read_text()
    _run_update(tmp_target, dry_run=True)
    content_after = lock_path.read_text()
    assert content_before == content_after


def test_update_detects_changed_hash(tmp_target: Path):
    """Update detects when a source hash has changed."""
    _run_setup(tmp_target)

    # Tamper with a lock entry's hash to simulate a source change
    entries = read_lock(tmp_target)
    if entries:
        entries[0] = LockEntry(
            workflow_id=entries[0].workflow_id,
            tool=entries[0].tool,
            target_path=entries[0].target_path,
            source_hash="0000000000000000000000000000000000000000000000000000000000000000",
            installed_at=entries[0].installed_at,
        )
        write_lock(tmp_target, entries)

    _run_update(tmp_target)

    # After update, the hash should match the actual source
    updated = read_lock(tmp_target)
    first = next(e for e in updated if e.workflow_id == entries[0].workflow_id)
    assert first.source_hash != "0000000000000000000000000000000000000000000000000000000000000000"


def test_update_preserves_entry_count(tmp_target: Path):
    """Update preserves the number of lock entries."""
    _run_setup(tmp_target)
    count_before = len(read_lock(tmp_target))
    _run_update(tmp_target, force=True)
    count_after = len(read_lock(tmp_target))
    assert count_before == count_after
