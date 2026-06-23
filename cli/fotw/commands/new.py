"""Create new workflow files from templates."""

import os
import subprocess
import sys
from pathlib import Path
from typing import Optional

import typer

from fotw.models.workflow import _PLURAL_MAP
from fotw.services.catalog import WORKFLOWS_DIR
from fotw.ui.console import console, err_console

_VALID_TYPES = ("rule", "skill", "agent")


def _normalize_type(wtype: str) -> str:
    return _PLURAL_MAP.get(wtype, wtype)


def _check_exists(wtype: str, name: str) -> bool:
    if wtype == "rule":
        return (WORKFLOWS_DIR / "rules" / f"{name}.mdc").is_file() or \
               (WORKFLOWS_DIR / "rules" / f"{name}.md").is_file()
    elif wtype == "skill":
        return (WORKFLOWS_DIR / "skills" / name).is_dir()
    elif wtype == "agent":
        return (WORKFLOWS_DIR / "agents" / f"{name}.md").is_file()
    return False


def _create_rule(name: str, description: str) -> Path:
    target_dir = WORKFLOWS_DIR / "rules"
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / f"{name}.mdc"
    target.write_text(f"""---
description: {description}
globs: "**/*"
alwaysApply: false
---

# {name}

{description}

## Guidelines

- Guideline one
- Guideline two
- Guideline three
""")
    return target


def _create_skill(name: str, description: str) -> Path:
    target_dir = WORKFLOWS_DIR / "skills" / name
    (target_dir / "references").mkdir(parents=True, exist_ok=True)
    (target_dir / "scripts").mkdir(parents=True, exist_ok=True)
    (target_dir / "assets").mkdir(parents=True, exist_ok=True)

    skill_file = target_dir / "SKILL.md"
    skill_file.write_text(f"""---
name: {name}
description: {description}
# context: fork                    # Uncomment for isolated execution
# agent: agent-name                # Uncomment to link a subagent
# allowed-tools: Read, Grep        # Uncomment to restrict tools
# --- Claude Code only (ignored by Cursor) ---
# model: sonnet                    # opus, sonnet, haiku, inherit, or default
# argument-hint: "[args]"          # CLI autocomplete hint
# disable-model-invocation: false  # Set true to require /command
---

# {name}

{description}

## When to Use

- Use this skill when...
- This skill is helpful for...

## Instructions

1. Step one
2. Step two
3. Step three

## References

See `references/` for additional documentation.
""")

    (target_dir / "references" / "README.md").write_text(
        f"# References\n\nAdditional documentation for the {name} skill.\n"
    )

    return skill_file


def _create_agent(name: str, description: str) -> Path:
    target_dir = WORKFLOWS_DIR / "agents"
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / f"{name}.md"
    target.write_text(f"""---
name: {name}
description: {description}
tools: Bash, Glob, Grep, Read, Write
model: sonnet
---

# {name}

{description}

## Purpose

Describe what this agent specializes in.

## Instructions

- Instruction one
- Instruction two
- Instruction three
""")
    return target


def new_cmd(
    workflow_path: str = typer.Argument(
        ..., help="Workflow type and name (e.g., rule/code-style, skill/pr-review)"
    ),
    yes: bool = typer.Option(
        False, "--yes", "-y", help="Skip prompts, use defaults"
    ),
    no_edit: bool = typer.Option(
        False, "--no-edit", help="Don't open in $EDITOR after creation"
    ),
    description: Optional[str] = typer.Option(
        None, "--description", "-d", help="Workflow description"
    ),
) -> None:
    """Create a new workflow from template."""
    parts = workflow_path.split("/", 1)
    if len(parts) != 2:
        err_console.print("[red]Error: Invalid workflow path. Expected format: type/name[/red]")
        err_console.print("Example: fotw new rule/my-rule, fotw new skill/my-skill")
        raise typer.Exit(1)

    wtype, name = parts
    wtype = _normalize_type(wtype)

    if wtype not in _VALID_TYPES:
        err_console.print(f"[red]Error: Unknown type: {wtype}[/red]")
        err_console.print(f"Supported types: {', '.join(_VALID_TYPES)}")
        raise typer.Exit(1)

    # Duplicate detection
    if _check_exists(wtype, name):
        console.print(f"[yellow]Warning: {wtype}/{name} already exists[/yellow]")
        if yes:
            console.print("Overwriting (--yes).")
        else:
            if not sys.stdin.isatty():
                err_console.print("[red]Error: workflow exists (use --yes to overwrite)[/red]")
                raise typer.Exit(1)
            choice = console.input("Overwrite? [y/N] ").strip().lower()
            if choice != "y":
                console.print("Aborted.")
                raise typer.Exit(0)

    # Get description
    if description is None:
        if yes:
            description = "TODO: Add description"
        elif sys.stdin.isatty():
            console.print()
            console.print(f"Creating new {wtype}: {name}")
            console.print()
            description = console.input("Description: ").strip() or "TODO: Add description"
        else:
            description = "TODO: Add description"

    # Create the workflow
    console.print()
    if wtype == "rule":
        created = _create_rule(name, description)
        console.print(f"[green]\u2713[/green] Created rule at {created}")
        console.print("[yellow]Note:[/yellow] Rules are stored in Cursor format and translated automatically when installing for other tools")
    elif wtype == "skill":
        created = _create_skill(name, description)
        console.print(f"[green]\u2713[/green] Created skill at {created.parent}")
    elif wtype == "agent":
        created = _create_agent(name, description)
        console.print(f"[green]\u2713[/green] Created agent at {created}")

    # Editor
    editor = os.environ.get("EDITOR")
    if not no_edit and editor:
        console.print()
        console.print(f"Opening in {editor}...")
        try:
            subprocess.run([editor, str(created)], check=True)
        except FileNotFoundError:
            err_console.print(f"[red]Error: editor not found: {editor}[/red]")
        except subprocess.CalledProcessError as exc:
            err_console.print(f"[red]Error launching editor: {exc}[/red]")
    elif not no_edit and not editor:
        console.print()
        console.print("Set $EDITOR to automatically open new workflows")
        console.print(f"File created at: {created}")

    console.print()
    console.print("[green]Done![/green]")
