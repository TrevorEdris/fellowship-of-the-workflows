"""fotw uninstall — remove installed fotw artifacts from a target."""

from pathlib import Path

import typer

from fotw.services.agents import is_valid_tool, list_tools
from fotw.services.installer import InstallContext, uninstall_personas
from fotw.ui.console import err_console


def uninstall_cmd(
    workflow_id: str = typer.Argument(..., help="What to uninstall. Supported: personas"),
    target_repo: str = typer.Argument(None, help="Target repository path"),
    for_tool: str = typer.Option("claude-code", "--for", help="Tool target"),
    global_install: bool = typer.Option(False, "--global", help="Uninstall from the global config dir"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview what would be removed without changing anything"),
) -> None:
    """Remove installed artifacts (currently: personas and their output styles/settings)."""
    if workflow_id != "personas":
        err_console.print(f"[red]Error: Unknown uninstall target: {workflow_id}[/red]")
        err_console.print("Supported: personas")
        raise typer.Exit(1)

    if not is_valid_tool(for_tool):
        err_console.print(f"[red]Error: Invalid tool: {for_tool}[/red]")
        err_console.print(f"Supported: {', '.join(list_tools())}")
        raise typer.Exit(1)

    if not target_repo and not global_install:
        err_console.print("[red]Error: target-repo is required (or use --global)[/red]")
        raise typer.Exit(1)

    resolved_target = Path(target_repo).expanduser().resolve() if target_repo else Path.cwd()
    if target_repo and not resolved_target.is_dir():
        err_console.print(f"[red]Error: Target does not exist: {resolved_target}[/red]")
        raise typer.Exit(1)

    ctx = InstallContext(
        tool=for_tool, target_repo=resolved_target, is_global=global_install,
        dry_run=dry_run,
    )
    if not uninstall_personas(ctx):
        raise typer.Exit(1)
