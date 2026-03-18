"""Lock file model for tracking installed rules."""

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path


LOCK_FILENAME = ".fotw-lock.json"


@dataclass
class LockEntry:
    """A single entry in the lock file tracking an installed rule."""

    workflow_id: str       # e.g., "rules/git-safety"
    tool: str              # e.g., "claude-code"
    target_path: str       # e.g., ".claude/rules/git-safety.md"
    source_hash: str       # SHA256 of source file content
    installed_at: str      # ISO 8601 timestamp
    link_type: str = "copy"  # "symlink" | "copy" — default preserves backward compat


def compute_source_hash(path: Path) -> str:
    """Compute SHA256 hash of a file's content."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_lock(project_root: Path) -> list[LockEntry]:
    """Read lock entries from a project's lock file."""
    lock_path = project_root / LOCK_FILENAME
    if not lock_path.is_file():
        return []
    try:
        data = json.loads(lock_path.read_text())
        return [LockEntry(**entry) for entry in data.get("entries", [])]
    except (json.JSONDecodeError, TypeError, KeyError):
        return []


def write_lock(project_root: Path, entries: list[LockEntry]) -> None:
    """Write lock entries to a project's lock file."""
    lock_path = project_root / LOCK_FILENAME
    data = {
        "version": 1,
        "entries": [asdict(e) for e in entries],
    }
    lock_path.write_text(json.dumps(data, indent=2) + "\n")


def merge_lock(existing: list[LockEntry], new: list[LockEntry]) -> list[LockEntry]:
    """Merge new entries into existing, upserting by (workflow_id, tool)."""
    by_key: dict[tuple[str, str], LockEntry] = {}
    for entry in existing:
        by_key[(entry.workflow_id, entry.tool)] = entry
    for entry in new:
        by_key[(entry.workflow_id, entry.tool)] = entry
    return list(by_key.values())
