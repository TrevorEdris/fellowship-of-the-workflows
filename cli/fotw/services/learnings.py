"""Learnings management for per-skill improvement findings."""

import re
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

MAX_ENTRIES = 20
EXPIRY_DAYS = 30
EXPIRING_THRESHOLD_DAYS = 21

ENTRY_PATTERN = re.compile(
    r"^- \[(\d{4}-\d{2}-\d{2})\] (.+?) — Source: (\w[\w-]*) — Status: (\w+)$"
)


@dataclass
class LearningEntry:
    """A single learning entry."""
    date: date
    finding: str
    source: str
    status: str

    def to_line(self) -> str:
        return f"- [{self.date.isoformat()}] {self.finding} — Source: {self.source} — Status: {self.status}"


def _parse_entries(path: Path) -> list[LearningEntry]:
    """Parse learning entries from a learnings.md file."""
    if not path.is_file():
        return []
    entries = []
    for line in path.read_text().splitlines():
        m = ENTRY_PATTERN.match(line.strip())
        if m:
            entries.append(LearningEntry(
                date=date.fromisoformat(m.group(1)),
                finding=m.group(2),
                source=m.group(3),
                status=m.group(4),
            ))
    return entries


def _write_entries(path: Path, skill_name: str, entries: list[LearningEntry]) -> None:
    """Write entries back to learnings.md."""
    lines = [
        f"# Learnings: {skill_name}",
        "",
        "<!-- Staging area for skill improvement findings.",
        "     Promote valuable learnings to SKILL.md or references/.",
        "     Entries expire after 30 days. Max 20 active entries. -->",
        "",
        "## Active",
        "",
    ]
    for entry in entries:
        lines.append(entry.to_line())
    lines.append("")
    path.write_text("\n".join(lines))


def _update_statuses(entries: list[LearningEntry], today: date | None = None) -> list[LearningEntry]:
    """Update status fields based on age."""
    today = today or date.today()
    for entry in entries:
        age = (today - entry.date).days
        if age >= EXPIRING_THRESHOLD_DAYS:
            entry.status = "expiring"
        else:
            entry.status = "active"
    return entries


def append_learning(skill_dir: Path, finding: str, source: str, today: date | None = None) -> LearningEntry:
    """Add a learning entry. Enforces 20-entry cap by evicting oldest if full."""
    today = today or date.today()
    path = skill_dir / "learnings.md"
    skill_name = skill_dir.name

    entries = _parse_entries(path)

    # Evict oldest if at capacity
    while len(entries) >= MAX_ENTRIES:
        entries.pop(0)

    entry = LearningEntry(date=today, finding=finding, source=source, status="active")
    entries.append(entry)
    entries = _update_statuses(entries, today)
    _write_entries(path, skill_name, entries)
    return entry


def prune_expired(skill_dir: Path, today: date | None = None) -> list[LearningEntry]:
    """Remove entries older than 30 days. Returns removed entries."""
    today = today or date.today()
    path = skill_dir / "learnings.md"
    skill_name = skill_dir.name

    entries = _parse_entries(path)
    if not entries:
        return []

    cutoff = today - timedelta(days=EXPIRY_DAYS)
    kept = [e for e in entries if e.date > cutoff]
    removed = [e for e in entries if e.date <= cutoff]

    if removed:
        kept = _update_statuses(kept, today)
        _write_entries(path, skill_name, kept)

    return removed


def list_expiring(skill_dir: Path, threshold_days: int = EXPIRING_THRESHOLD_DAYS, today: date | None = None) -> list[LearningEntry]:
    """Return entries approaching expiry (older than threshold_days)."""
    today = today or date.today()
    path = skill_dir / "learnings.md"
    entries = _parse_entries(path)
    cutoff = today - timedelta(days=threshold_days)
    return [e for e in entries if e.date <= cutoff]
