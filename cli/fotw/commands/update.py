"""Update command — re-sync installed rules based on lock file."""

from datetime import datetime, timezone
from pathlib import Path

import typer

from fotw.models.lock import (
    LOCK_FILENAME,
    LockEntry,
    compute_source_hash,
    read_lock,
    write_lock,
)
from fotw.services.catalog import WORKFLOWS_DIR
from fotw.services.installer import InstallContext, install_single_workflow
from fotw.ui.console import console, err_console


def update_cmd(
    target_repo: str = typer.Argument(
        ..., help="Path to target project"
    ),
    force: bool = typer.Option(
        False, "--force", "-f", help="Re-install everything regardless of hash"
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run", "-n", help="Show what would change without changing"
    ),
) -> None:
    """Re-sync installed rules based on the lock file."""
    resolved = Path(target_repo).expanduser().resolve()

    if not resolved.is_dir():
        err_console.print(f"[red]Error: Target does not exist: {resolved}[/red]")
        raise typer.Exit(1)

    entries = read_lock(resolved)
    if not entries:
        err_console.print(f"[red]Error: No lock file found at {resolved / LOCK_FILENAME}[/red]")
        err_console.print("Run 'fotw setup' first to create one.")
        raise typer.Exit(1)

    console.print()
    console.print(f"Updating rules in {resolved}")
    console.print(f"Lock entries: {len(entries)}")
    console.print()

    updated = 0
    unchanged = 0
    errors = 0
    updated_entries: list[LockEntry] = []
    now = datetime.now(timezone.utc).isoformat()

    for entry in entries:
        # Resolve source file from workflow_id
        parts = entry.workflow_id.split("/", 1)
        if len(parts) != 2:
            console.print(f"  [red]\u2717[/red] Invalid workflow_id: {entry.workflow_id}")
            errors += 1
            updated_entries.append(entry)
            continue

        wtype, name = parts
        source = _find_source(wtype, name)
        if source is None:
            console.print(f"  [red]\u2717[/red] Source not found: {entry.workflow_id}")
            errors += 1
            updated_entries.append(entry)
            continue

        current_hash = compute_source_hash(source)
        needs_update = force or current_hash != entry.source_hash

        if entry.link_type == "symlink":
            target = resolved / entry.target_path
            # Verify symlink is still valid.
            if target.is_symlink() and target.exists() and not needs_update:
                console.print(f"  [dim]\u2022[/dim] {entry.workflow_id} (symlink current)")
                unchanged += 1
                updated_entries.append(entry)
                continue

            if needs_update:
                # For translated rules: regenerate the cache file; symlink is unchanged.
                from fotw.services.agents import get_agent_config
                from fotw.services.cache import build_cache_file, get_cache_path
                cfg = get_agent_config(entry.tool)
                if cfg is not None and wtype == "rules" and cfg.frontmatter_format != "cursor":
                    if dry_run:
                        console.print(f"  [yellow][DRY RUN][/yellow] Would regenerate cache for {entry.workflow_id}")
                    else:
                        build_cache_file(source, wtype, cfg)
                        console.print(f"  [green]\u2713[/green] {entry.workflow_id} (cache updated)")
                    updated += 1
                    updated_entries.append(
                        LockEntry(
                            workflow_id=entry.workflow_id,
                            tool=entry.tool,
                            target_path=entry.target_path,
                            source_hash=current_hash,
                            installed_at=now,
                            link_type="symlink",
                        )
                    )
                    continue
            # Broken or missing symlink — re-install.
            if dry_run:
                console.print(f"  [yellow][DRY RUN][/yellow] Would re-symlink {entry.workflow_id}")
                updated += 1
                updated_entries.append(entry)
                continue
            ctx = InstallContext(
                tool=entry.tool,
                target_repo=resolved,
                force=True,
                quiet=True,
            )
            if install_single_workflow(entry.workflow_id, ctx):
                console.print(f"  [green]\u2713[/green] {entry.workflow_id} (re-symlinked)")
                updated += 1
                updated_entries.append(
                    LockEntry(
                        workflow_id=entry.workflow_id,
                        tool=entry.tool,
                        target_path=entry.target_path,
                        source_hash=current_hash,
                        installed_at=now,
                        link_type="symlink",
                    )
                )
            else:
                console.print(f"  [red]\u2717[/red] {entry.workflow_id} (failed)")
                errors += 1
                updated_entries.append(entry)
            continue

        # Legacy copy-based entry.
        if not needs_update:
            console.print(f"  [dim]\u2022[/dim] {entry.workflow_id} (unchanged)")
            unchanged += 1
            updated_entries.append(entry)
            continue

        if dry_run:
            console.print(f"  [yellow][DRY RUN][/yellow] Would update {entry.workflow_id}")
            updated += 1
            updated_entries.append(entry)
            continue

        ctx = InstallContext(
            tool=entry.tool,
            target_repo=resolved,
            force=True,
            quiet=True,
        )

        if install_single_workflow(entry.workflow_id, ctx):
            console.print(f"  [green]\u2713[/green] {entry.workflow_id} (updated)")
            updated += 1
            updated_entries.append(
                LockEntry(
                    workflow_id=entry.workflow_id,
                    tool=entry.tool,
                    target_path=entry.target_path,
                    source_hash=current_hash,
                    installed_at=now,
                )
            )
        else:
            console.print(f"  [red]\u2717[/red] {entry.workflow_id} (failed)")
            errors += 1
            updated_entries.append(entry)

    # Write updated lock file
    if not dry_run:
        write_lock(resolved, updated_entries)

    # Summary
    console.print()
    if dry_run:
        console.print(f"[yellow][DRY RUN] {updated} would be updated, {unchanged} unchanged, {errors} errors[/yellow]")
    else:
        console.print(f"[green]Update complete:[/green] {updated} updated, {unchanged} unchanged, {errors} errors")


def _find_source(wtype: str, name: str) -> Path | None:
    """Find the source file for a workflow by type and name."""
    if wtype == "rules":
        mdc = WORKFLOWS_DIR / "rules" / f"{name}.mdc"
        if mdc.is_file():
            return mdc
        md = WORKFLOWS_DIR / "rules" / f"{name}.md"
        if md.is_file():
            return md
    return None
