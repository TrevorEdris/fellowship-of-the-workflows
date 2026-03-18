"""Resolve context files for a skill based on its context manifest and active phase."""

from pathlib import Path

import frontmatter


VALID_PHASES = {"discover", "plan", "implement"}


def resolve_context(skill_dir: Path, phase: str | None = None) -> list[Path]:
    """Given a skill directory and optional phase, return the list of files to include.

    Rules:
    1. If no context-manifest in SKILL.md frontmatter -> return all files (backward compat)
    2. If manifest exists and phase is None -> return 'always' files only
    3. If manifest exists and phase given -> return union of 'always' + phase-specific files
    4. Files are relative to skill_dir
    """
    skill_file = skill_dir / "SKILL.md"
    if not skill_file.is_file():
        return []

    post = frontmatter.load(str(skill_file))
    manifest = post.metadata.get("context-manifest")

    if manifest is None:
        # No manifest -> include everything (backward compatible)
        return _all_files(skill_dir)

    files: list[Path] = []

    # Always include SKILL.md itself
    files.append(skill_file)

    # Always-included files
    always = manifest.get("always", [])
    for rel_path in always:
        abs_path = skill_dir / rel_path
        if abs_path.is_file() and abs_path not in files:
            files.append(abs_path)

    # Phase-specific files
    if phase and phase in manifest:
        for rel_path in manifest[phase]:
            abs_path = skill_dir / rel_path
            if abs_path.is_file() and abs_path not in files:
                files.append(abs_path)

    return files


def _all_files(skill_dir: Path) -> list[Path]:
    """Return all files in a skill directory (recursive)."""
    return sorted(f for f in skill_dir.rglob("*") if f.is_file())
