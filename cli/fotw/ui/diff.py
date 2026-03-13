"""Rich-formatted unified diff display."""

import difflib
from pathlib import Path

from rich.panel import Panel
from rich.syntax import Syntax

from fotw.ui.console import console


def show_diff(existing_content: str, new_content: str, filename: str) -> None:
    """Display a colored unified diff between existing and new content."""
    existing_lines = existing_content.splitlines(keepends=True)
    new_lines = new_content.splitlines(keepends=True)

    diff_lines = list(
        difflib.unified_diff(
            existing_lines,
            new_lines,
            fromfile=f"existing/{filename}",
            tofile=f"new/{filename}",
        )
    )

    if not diff_lines:
        console.print("[green]Files are identical[/green]")
        return

    diff_text = "".join(diff_lines)
    syntax = Syntax(diff_text, "diff", theme="monokai", line_numbers=False)
    panel = Panel(syntax, title=f"Diff: {filename}", border_style="yellow")
    with console.pager(styles=True):
        console.print(panel)


def show_dir_diff(existing_dir: Path, source_dir: Path, dirname: str) -> None:
    """Display a combined unified diff for all files in two directories."""
    existing_files = {
        f.relative_to(existing_dir): f
        for f in sorted(existing_dir.rglob("*")) if f.is_file()
    }
    source_files = {
        f.relative_to(source_dir): f
        for f in sorted(source_dir.rglob("*")) if f.is_file()
    }

    all_keys = sorted(set(existing_files) | set(source_files))
    all_diff_lines: list[str] = []

    for key in all_keys:
        existing_path = existing_files.get(key)
        source_path = source_files.get(key)
        old_lines = existing_path.read_text().splitlines(keepends=True) if existing_path else []
        new_lines = source_path.read_text().splitlines(keepends=True) if source_path else []

        diff_lines = list(difflib.unified_diff(
            old_lines, new_lines,
            fromfile=f"existing/{dirname}/{key}",
            tofile=f"new/{dirname}/{key}",
        ))
        if diff_lines:
            all_diff_lines.extend(diff_lines)

    if not all_diff_lines:
        console.print("[green]Directories are identical[/green]")
        return

    diff_text = "".join(all_diff_lines)
    syntax = Syntax(diff_text, "diff", theme="monokai", line_numbers=False)
    panel = Panel(syntax, title=f"Diff: {dirname}/", border_style="yellow")
    with console.pager(styles=True):
        console.print(panel)


def files_are_identical(existing_content: str, new_content: str) -> bool:
    """Check if two file contents are identical (ignoring trailing whitespace)."""
    return existing_content.rstrip() == new_content.rstrip()


def dirs_are_identical(existing_dir: Path, source_dir: Path) -> bool:
    """Check if two directories have identical file contents recursively."""
    existing_files = {
        f.relative_to(existing_dir): f
        for f in sorted(existing_dir.rglob("*")) if f.is_file()
    }
    source_files = {
        f.relative_to(source_dir): f
        for f in sorted(source_dir.rglob("*")) if f.is_file()
    }

    if set(existing_files) != set(source_files):
        return False

    return all(
        files_are_identical(
            existing_files[key].read_text(),
            source_files[key].read_text(),
        )
        for key in existing_files
    )
