"""Rich-formatted unified diff display."""

import difflib

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
    console.print(Panel(syntax, title=f"Diff: {filename}", border_style="yellow"))


def files_are_identical(existing_content: str, new_content: str) -> bool:
    """Check if two file contents are identical (ignoring trailing whitespace)."""
    return existing_content.rstrip() == new_content.rstrip()
