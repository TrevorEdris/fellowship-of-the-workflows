"""Setup command — install rules to a target project with lock file tracking."""

from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import typer

from fotw.models.lock import (
    LOCK_FILENAME,
    LockEntry,
    compute_source_hash,
    merge_lock,
    read_lock,
    write_lock,
)
from fotw.services.agents import get_agent_config, is_valid_tool, list_tools
from fotw.services.catalog import scan_rules
from fotw.services.installer import InstallContext, install_single_workflow
from fotw.ui.console import console, err_console


def setup_cmd(
    target_repo: str = typer.Argument(
        ..., help="Path to target project"
    ),
    for_tool: str = typer.Option(
        ..., "--for", help="Target tool (e.g., claude-code, cursor, copilot)"
    ),
    force: bool = typer.Option(
        False, "--force", "-f", help="Overwrite existing files without prompting"
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run", "-n", help="Show what would be installed without installing"
    ),
    rules_only: bool = typer.Option(
        True, "--rules-only/--all-types", help="Only install rules (default; skills/agents come via plugin)"
    ),
) -> None:
    """Install rules to a target project and create a lock file for tracking."""
    resolved = Path(target_repo).expanduser().resolve()

    if not resolved.is_dir():
        err_console.print(f"[red]Error: Target does not exist: {resolved}[/red]")
        raise typer.Exit(1)

    if not is_valid_tool(for_tool):
        err_console.print(f"[red]Error: Invalid tool: {for_tool}[/red]")
        err_console.print(f"Supported: {', '.join(list_tools())}")
        raise typer.Exit(1)

    cfg = get_agent_config(for_tool)
    if cfg is None:
        err_console.print(f"[red]Error: No config for tool: {for_tool}[/red]")
        raise typer.Exit(1)

    rules = scan_rules()
    if not rules:
        console.print("[yellow]No rules found in catalog[/yellow]")
        return

    console.print()
    console.print(f"Setting up rules for [bold]{cfg.name}[/bold] in {resolved}")
    console.print(f"Rules found: {len(rules)}")
    console.print()

    ctx = InstallContext(
        tool=for_tool,
        target_repo=resolved,
        force=force,
        dry_run=dry_run,
        quiet=True,
    )

    new_entries: list[LockEntry] = []
    succeeded = 0
    failed = 0
    now = datetime.now(timezone.utc).isoformat()

    for rule in rules:
        wf_id = rule.workflow_id
        source = rule.path

        if dry_run:
            target_name = source.stem + cfg.rule_extension
            target_path = resolved / cfg.config_dir / cfg.rules_subdir / target_name
            console.print(f"  [yellow][DRY RUN][/yellow] Would install {wf_id} -> {target_path}")
            succeeded += 1
            continue

        if install_single_workflow(wf_id, ctx):
            target_name = source.stem + cfg.rule_extension
            rel_target = f"{cfg.config_dir}/{cfg.rules_subdir}/{target_name}"
            new_entries.append(
                LockEntry(
                    workflow_id=wf_id,
                    tool=for_tool,
                    target_path=rel_target,
                    source_hash=compute_source_hash(source),
                    installed_at=now,
                )
            )
            console.print(f"  [green]\u2713[/green] {wf_id}")
            succeeded += 1
        else:
            console.print(f"  [red]\u2717[/red] {wf_id}")
            failed += 1

    # Update lock file
    if not dry_run and new_entries:
        existing = read_lock(resolved)
        merged = merge_lock(existing, new_entries)
        write_lock(resolved, merged)

    # Summary
    console.print()
    if dry_run:
        console.print(f"[yellow][DRY RUN] Would install {succeeded} rules[/yellow]")
    else:
        console.print(f"[green]Setup complete:[/green] {succeeded} installed, {failed} failed")
        if new_entries:
            console.print(f"Lock file: {resolved / LOCK_FILENAME}")
