"""Install workflows, starters, and personas to target projects."""

from pathlib import Path
from typing import Optional

import typer

from fotw.services.installer import (
    InstallContext,
    InstallQuit,
    install_all,
    install_personas,
    install_single_workflow,
    install_starter,
)
from fotw.ui.console import console, err_console

VALID_TOOLS = ("cursor", "claude-code")
VALID_STARTER_TOOLS = ("cursor", "claude-code", "both")


def _normalize_workflow_id(wf_id: str) -> str:
    """Normalize singular prefixes to plural (rule/ -> rules/)."""
    mapping = {
        "rule/": "rules/",
        "skill/": "skills/",
        "agent/": "agents/",
        "starter/": "starters/",
    }
    for singular, plural in mapping.items():
        if wf_id.startswith(singular):
            return plural + wf_id[len(singular):]
    return wf_id


def install_cmd(
    workflow_id: Optional[str] = typer.Argument(
        None, help="Workflow to install (e.g., rules/ai-session, starters/standard, personas)"
    ),
    target_repo: Optional[str] = typer.Argument(
        None, help="Path to target repository"
    ),
    for_tool: str = typer.Option(
        ..., "--for", help="Target tool: cursor, claude-code, or both (starters only)"
    ),
    all_workflows: bool = typer.Option(
        False, "--all", "-a", help="Install all available workflows"
    ),
    force: bool = typer.Option(
        False, "--force", "-f", help="Overwrite existing files without prompting"
    ),
    global_install: bool = typer.Option(
        False, "--global", "-g", help="Install globally to ~/.<tool>/"
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run", "-n", help="Show what would be copied without copying"
    ),
    to_claude_dir: bool = typer.Option(
        False, "--to-claude-dir", help="Install CLAUDE.md to .claude/ directory"
    ),
) -> None:
    """Install workflows, starters, or personas to a target project."""
    try:
        _install_cmd_inner(
            workflow_id, target_repo, for_tool, all_workflows,
            force, global_install, dry_run, to_claude_dir,
        )
    except InstallQuit:
        console.print("\nQuit.")
        raise typer.Exit(0)


def _install_cmd_inner(
    workflow_id: str | None,
    target_repo: str | None,
    for_tool: str,
    all_workflows: bool,
    force: bool,
    global_install: bool,
    dry_run: bool,
    to_claude_dir: bool,
) -> None:
    # When --all is used, the first positional arg is the target repo, not workflow_id.
    # Same for paths that look like directories (start with /, ~, .).
    if workflow_id and not target_repo:
        if all_workflows or (
            workflow_id.startswith("/")
            or workflow_id.startswith("~")
            or workflow_id.startswith(".")
        ):
            target_repo = workflow_id
            workflow_id = None

    # Normalize workflow_id
    if workflow_id:
        workflow_id = _normalize_workflow_id(workflow_id)

    # Resolve target_repo
    resolved_target = Path(target_repo).expanduser().resolve() if target_repo else Path.cwd()

    # --- Personas standalone ---
    if workflow_id == "personas":
        if for_tool not in VALID_TOOLS:
            err_console.print(f"[red]Error: Invalid tool for personas: {for_tool}[/red]")
            err_console.print(f"Supported: {', '.join(VALID_TOOLS)}")
            raise typer.Exit(1)

        if not target_repo and not global_install:
            err_console.print("[red]Error: target-repo is required (or use --global)[/red]")
            raise typer.Exit(1)

        if target_repo and not resolved_target.is_dir():
            err_console.print(f"[red]Error: Target does not exist: {resolved_target}[/red]")
            raise typer.Exit(1)

        ctx = InstallContext(
            tool=for_tool, target_repo=resolved_target,
            is_global=global_install, dry_run=dry_run, force=force,
        )
        if install_personas(ctx):
            console.print()
            console.print("[green]Personas installed![/green]")
        else:
            raise typer.Exit(1)
        return

    # --- Starters ---
    if workflow_id and workflow_id.startswith("starters/"):
        tier = workflow_id.split("/", 1)[1]

        if not target_repo:
            err_console.print("[red]Error: target-repo is required for starters[/red]")
            raise typer.Exit(1)

        if not resolved_target.is_dir():
            err_console.print(f"[red]Error: Target does not exist: {resolved_target}[/red]")
            raise typer.Exit(1)

        if for_tool not in VALID_STARTER_TOOLS:
            err_console.print(f"[red]Error: Invalid tool for starters: {for_tool}[/red]")
            err_console.print(f"Supported: {', '.join(VALID_STARTER_TOOLS)}")
            raise typer.Exit(1)

        ctx = InstallContext(
            tool=for_tool, target_repo=resolved_target,
            dry_run=dry_run, force=force, to_claude_dir=to_claude_dir,
        )
        if install_starter(tier, ctx):
            console.print()
            console.print("[green]Installation complete![/green]")
        else:
            raise typer.Exit(1)
        return

    # --- From here on, --for must be cursor or claude-code ---
    if for_tool not in VALID_TOOLS:
        err_console.print(f"[red]Error: Invalid tool: {for_tool}[/red]")
        err_console.print(f"Supported: {', '.join(VALID_TOOLS)}")
        raise typer.Exit(1)

    # --- Install all ---
    if all_workflows:
        if not target_repo and not global_install:
            err_console.print("[red]Error: target-repo is required with --all (or use --global)[/red]")
            raise typer.Exit(1)

        if target_repo and not resolved_target.is_dir():
            err_console.print(f"[red]Error: Target does not exist: {resolved_target}[/red]")
            raise typer.Exit(1)

        ctx = InstallContext(
            tool=for_tool, target_repo=resolved_target,
            is_global=global_install, dry_run=dry_run, force=force,
        )
        if not install_all(ctx):
            raise typer.Exit(1)
        return

    # --- Single workflow ---
    if not workflow_id:
        err_console.print("[red]Error: workflow-id is required[/red]")
        err_console.print("Example: fotw install rules/ai-session ~/my-repo --for claude-code")
        raise typer.Exit(1)

    if not target_repo and not global_install:
        err_console.print("[red]Error: target-repo is required (or use --global)[/red]")
        raise typer.Exit(1)

    if target_repo and not resolved_target.is_dir():
        err_console.print(f"[red]Error: Target does not exist: {resolved_target}[/red]")
        raise typer.Exit(1)

    ctx = InstallContext(
        tool=for_tool, target_repo=resolved_target,
        is_global=global_install, dry_run=dry_run, force=force,
    )
    if install_single_workflow(workflow_id, ctx):
        console.print()
        console.print("[green]Installation complete![/green]")
    else:
        raise typer.Exit(1)
