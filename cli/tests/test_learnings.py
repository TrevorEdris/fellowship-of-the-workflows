"""Tests for learnings management service."""

from datetime import date, timedelta

import pytest

from fotw.services.learnings import (
    MAX_ENTRIES,
    LearningEntry,
    append_learning,
    list_expiring,
    prune_expired,
    _parse_entries,
)


class TestAppendLearning:
    def test_creates_file_if_missing(self, tmp_path):
        skill_dir = tmp_path / "test-skill"
        skill_dir.mkdir()
        entry = append_learning(skill_dir, "test finding", "eval", today=date(2026, 3, 22))
        assert entry.finding == "test finding"
        assert entry.source == "eval"
        assert (skill_dir / "learnings.md").is_file()

    def test_appends_to_existing(self, tmp_path):
        skill_dir = tmp_path / "test-skill"
        skill_dir.mkdir()
        append_learning(skill_dir, "first", "eval", today=date(2026, 3, 22))
        append_learning(skill_dir, "second", "user", today=date(2026, 3, 23))
        entries = _parse_entries(skill_dir / "learnings.md")
        assert len(entries) == 2
        assert entries[0].finding == "first"
        assert entries[1].finding == "second"

    def test_enforces_cap(self, tmp_path):
        skill_dir = tmp_path / "test-skill"
        skill_dir.mkdir()
        for i in range(MAX_ENTRIES):
            append_learning(skill_dir, f"entry-{i}", "eval", today=date(2026, 3, 1) + timedelta(days=i))

        # One more should evict the oldest
        append_learning(skill_dir, "overflow", "eval", today=date(2026, 3, 22))
        entries = _parse_entries(skill_dir / "learnings.md")
        assert len(entries) == MAX_ENTRIES
        assert entries[0].finding == "entry-1"  # entry-0 evicted
        assert entries[-1].finding == "overflow"

    def test_sets_active_status(self, tmp_path):
        skill_dir = tmp_path / "test-skill"
        skill_dir.mkdir()
        entry = append_learning(skill_dir, "new", "eval", today=date(2026, 3, 22))
        assert entry.status == "active"


class TestPruneExpired:
    def test_removes_old_entries(self, tmp_path):
        skill_dir = tmp_path / "test-skill"
        skill_dir.mkdir()
        today = date(2026, 3, 22)
        append_learning(skill_dir, "old", "eval", today=today - timedelta(days=31))
        append_learning(skill_dir, "recent", "eval", today=today)

        removed = prune_expired(skill_dir, today=today)
        assert len(removed) == 1
        assert removed[0].finding == "old"

        remaining = _parse_entries(skill_dir / "learnings.md")
        assert len(remaining) == 1
        assert remaining[0].finding == "recent"

    def test_no_op_when_nothing_expired(self, tmp_path):
        skill_dir = tmp_path / "test-skill"
        skill_dir.mkdir()
        today = date(2026, 3, 22)
        append_learning(skill_dir, "recent", "eval", today=today)
        removed = prune_expired(skill_dir, today=today)
        assert len(removed) == 0

    def test_no_op_on_missing_file(self, tmp_path):
        skill_dir = tmp_path / "test-skill"
        skill_dir.mkdir()
        removed = prune_expired(skill_dir)
        assert removed == []


class TestListExpiring:
    def test_finds_expiring_entries(self, tmp_path):
        skill_dir = tmp_path / "test-skill"
        skill_dir.mkdir()
        today = date(2026, 3, 22)
        append_learning(skill_dir, "old-ish", "eval", today=today - timedelta(days=22))
        append_learning(skill_dir, "recent", "eval", today=today)

        expiring = list_expiring(skill_dir, today=today)
        assert len(expiring) == 1
        assert expiring[0].finding == "old-ish"

    def test_empty_when_all_fresh(self, tmp_path):
        skill_dir = tmp_path / "test-skill"
        skill_dir.mkdir()
        today = date(2026, 3, 22)
        append_learning(skill_dir, "fresh", "eval", today=today)
        expiring = list_expiring(skill_dir, today=today)
        assert len(expiring) == 0


class TestStatusUpdate:
    def test_marks_expiring(self, tmp_path):
        skill_dir = tmp_path / "test-skill"
        skill_dir.mkdir()
        today = date(2026, 3, 22)
        append_learning(skill_dir, "will-expire", "eval", today=today - timedelta(days=22))
        entries = _parse_entries(skill_dir / "learnings.md")
        # Re-add a fresh entry to trigger status update
        append_learning(skill_dir, "fresh", "eval", today=today)
        entries = _parse_entries(skill_dir / "learnings.md")
        assert entries[0].status == "expiring"
        assert entries[1].status == "active"
