"""Estimate token budget for skills and their reference files."""

from dataclasses import dataclass
from pathlib import Path


@dataclass
class FileBudget:
    """Token estimate for a single file."""
    path: Path
    chars: int
    estimated_tokens: int


@dataclass
class SkillBudget:
    """Token budget for an entire skill."""
    name: str
    files: list[FileBudget]
    total_chars: int
    total_tokens: int

    @property
    def file_count(self) -> int:
        return len(self.files)


# Rough approximation: 1 token ~ 4 characters for English text / code
CHARS_PER_TOKEN = 4


def estimate_file(path: Path) -> FileBudget:
    """Estimate tokens for a single file."""
    try:
        chars = len(path.read_text())
    except Exception:
        chars = 0
    return FileBudget(
        path=path,
        chars=chars,
        estimated_tokens=chars // CHARS_PER_TOKEN,
    )


def estimate_skill(skill_dir: Path) -> SkillBudget:
    """Estimate total token budget for a skill directory."""
    files = []
    total_chars = 0

    for path in sorted(skill_dir.rglob("*")):
        if not path.is_file():
            continue
        # Skip binary files, test files
        if path.suffix in (".png", ".jpg", ".gif", ".ico", ".woff", ".woff2"):
            continue
        if "tests/" in str(path.relative_to(skill_dir)):
            continue
        fb = estimate_file(path)
        files.append(fb)
        total_chars += fb.chars

    return SkillBudget(
        name=skill_dir.name,
        files=files,
        total_chars=total_chars,
        total_tokens=total_chars // CHARS_PER_TOKEN,
    )
