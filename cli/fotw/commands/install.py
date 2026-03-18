"""Install workflows, starters, and personas to target projects."""

from pathlib import Path
from typing import Optional

import typer

from fotw.services.agents import BOTH_TARGET, expand_tools, is_valid_tool, list_tools
from fotw.services.installer import (
    InstallContext,
    InstallQuit,
    install_all,
    install_filtered,
    install_hooks,
    install_personas,
    install_single_hook,
    install_single_workflow,
    install_starter,
)
from fotw.ui.console import console, err_console

_VALID_TYPE_FILTERS = {"rule", "skill", "agent"}
_VALID_TIER_FILTERS = {"core", "languages", "platforms", "vendors"}


def _normalize_workflow_id(wf_id: str) -> str:
    """Normalize singular prefixes to plural (rule/ -> rules/). Tier paths pass through unchanged."""
    mapping = {
        "rule/": "rules/",
        "skill/": "skills/",
        "agent/": "agents/",
        "starter/": "starters/",
        "hook/": "hooks/",
        "roster/": "rosters/",
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
        ..., "--for", help="Target tool (e.g., claude-code, cursor, copilot, codex, windsurf, roo, gemini, goose, universal, both)"
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
    include_tests: bool = typer.Option(
        False, "--include-tests", help="Also install hook test files"
    ),
    phase: Optional[str] = typer.Option(
        None, "--phase", help="Install phase-scoped context only (discover/plan/implement)"
    ),
    type_filter: Optional[str] = typer.Option(
        None, "--type", "-T", help="Filter by type (rule, skill, agent)"
    ),
    tier_filter: Optional[str] = typer.Option(
        None, "--tier", help="Filter by tier (core, languages, platforms, vendors)"
    ),
    tags: Optional[list[str]] = typer.Option(
        None, "--tag", "-t", help="Filter by tag (repeatable, AND logic)"
    ),
) -> None:
    """Install workflows, starters, or personas to a target project."""
    try:
        _install_cmd_inner(
            workflow_id, target_repo, for_tool, all_workflows,
            force, global_install, dry_run, to_claude_dir, include_tests, phase,
            type_filter, tier_filter, tags,
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
    include_tests: bool = False,
    phase: str | None = None,
    type_filter: str | None = None,
    tier_filter: str | None = None,
    tags: list[str] | None = None,
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
        if not is_valid_tool(for_tool):
            err_console.print(f"[red]Error: Invalid tool: {for_tool}[/red]")
            err_console.print(f"Supported: {', '.join(list_tools())}, both")
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

        if not is_valid_tool(for_tool):
            err_console.print(f"[red]Error: Invalid tool: {for_tool}[/red]")
            err_console.print(f"Supported: {', '.join(list_tools())}, both")
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

    # --- Rosters (roles) ---
    if workflow_id and workflow_id.startswith("rosters/"):
        role_name = workflow_id.split("/", 1)[1]

        if not target_repo and not global_install:
            err_console.print("[red]Error: target-repo is required for roles (or use --global)[/red]")
            raise typer.Exit(1)

        if target_repo and not resolved_target.is_dir():
            err_console.print(f"[red]Error: Target does not exist: {resolved_target}[/red]")
            raise typer.Exit(1)

        if not is_valid_tool(for_tool):
            err_console.print(f"[red]Error: Invalid tool: {for_tool}[/red]")
            err_console.print(f"Supported: {', '.join(list_tools())}, both")
            raise typer.Exit(1)

        from fotw.services.installer import install_role
        ctx = InstallContext(
            tool=for_tool, target_repo=resolved_target,
            is_global=global_install, dry_run=dry_run, force=force,
        )
        if install_role(role_name, ctx):
            console.print()
            console.print("[green]Role installation complete![/green]")
        else:
            raise typer.Exit(1)
        return

    # --- Hooks ---
    if workflow_id and (workflow_id == "hooks" or workflow_id.startswith("hooks/")):
        if not global_install:
            err_console.print("[red]Error: Hooks must be installed globally (--global)[/red]")
            raise typer.Exit(1)
        if for_tool != "claude-code":
            err_console.print("[red]Error: Hooks are only supported for claude-code[/red]")
            raise typer.Exit(1)

        ctx = InstallContext(
            tool="claude-code", target_repo=Path.home(),
            is_global=True, dry_run=dry_run, force=force,
        )

        if workflow_id == "hooks":
            if install_hooks(ctx, include_tests):
                console.print()
                console.print("[green]Hooks installed![/green]")
            else:
                raise typer.Exit(1)
        else:
            # Single hook: hooks/<name>
            hook_name = workflow_id.split("/", 1)[1]
            from fotw.services.catalog import scan_hooks
            hooks = scan_hooks()
            hook = next((h for h in hooks if h.name == hook_name), None)
            if not hook:
                err_console.print(f"[red]Error: Hook not found: {hook_name}[/red]")
                raise typer.Exit(1)
            if install_single_hook(hook, ctx, include_tests):
                # Also merge this single hook into settings
                from fotw.services.settings_merger import merge_hooks as _merge, read_settings, write_settings
                if not dry_run:
                    settings_path = Path.home() / ".claude" / "settings.json"
                    existing = read_settings(settings_path)
                    merged = _merge(existing, [hook])
                    write_settings(merged, settings_path)
                    if not ctx.quiet:
                        console.print(f"[green]\u2713[/green] Merged hook config into settings.json")
                console.print()
                console.print("[green]Hook installed![/green]")
            else:
                raise typer.Exit(1)
        return

    # --- From here on, --for must be a valid agent target ---
    if not is_valid_tool(for_tool):
        err_console.print(f"[red]Error: Invalid tool: {for_tool}[/red]")
        err_console.print(f"Supported: {', '.join(list_tools())}")
        raise typer.Exit(1)

    # Expand "both" into individual tools for non-starter paths
    tools = expand_tools(for_tool)

    # --- Install all ---
    if all_workflows:
        if not target_repo and not global_install:
            err_console.print("[red]Error: target-repo is required with --all (or use --global)[/red]")
            raise typer.Exit(1)

        if target_repo and not resolved_target.is_dir():
            err_console.print(f"[red]Error: Target does not exist: {resolved_target}[/red]")
            raise typer.Exit(1)

        any_failed = False
        for t in tools:
            ctx = InstallContext(
                tool=t, target_repo=resolved_target,
                is_global=global_install, dry_run=dry_run, force=force,
            )
            if not install_all(ctx):
                any_failed = True
        if any_failed:
            raise typer.Exit(1)
        return

    # --- Filtered install ---
    if type_filter or tier_filter or tags:
        # Validate filter values
        if type_filter and type_filter not in _VALID_TYPE_FILTERS:
            err_console.print(f"[red]Error: Invalid --type: {type_filter}[/red]")
            err_console.print(f"Valid types: {', '.join(sorted(_VALID_TYPE_FILTERS))}")
            raise typer.Exit(1)

        if tier_filter and tier_filter not in _VALID_TIER_FILTERS:
            err_console.print(f"[red]Error: Invalid --tier: {tier_filter}[/red]")
            err_console.print(f"Valid tiers: {', '.join(sorted(_VALID_TIER_FILTERS))}")
            raise typer.Exit(1)

        if tags:
            from fotw.models.workflow import VALID_TAGS
            bad_tags = [t for t in tags if t not in VALID_TAGS]
            if bad_tags:
                err_console.print(f"[red]Error: Invalid tags: {bad_tags}[/red]")
                err_console.print(f"Valid tags: {', '.join(sorted(VALID_TAGS))}")
                raise typer.Exit(1)

        if not target_repo and not global_install:
            err_console.print("[red]Error: target-repo is required with filters (or use --global)[/red]")
            raise typer.Exit(1)

        if target_repo and not resolved_target.is_dir():
            err_console.print(f"[red]Error: Target does not exist: {resolved_target}[/red]")
            raise typer.Exit(1)

        from fotw.services.catalog import filter_workflows, scan_all
        workflows = scan_all()
        workflows = filter_workflows(workflows, type_filter, tier_filter, tags)

        if not workflows:
            err_console.print("[yellow]No workflows match the given filters.[/yellow]")
            raise typer.Exit(0)

        console.print(f"Found {len(workflows)} matching workflow(s).")

        any_failed = False
        for t in tools:
            ctx = InstallContext(
                tool=t, target_repo=resolved_target,
                is_global=global_install, dry_run=dry_run, force=force,
            )
            if not install_filtered(workflows, ctx):
                any_failed = True
        if any_failed:
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

    for t in tools:
        ctx = InstallContext(
            tool=t, target_repo=resolved_target,
            is_global=global_install, dry_run=dry_run, force=force,
        )

        # Phase-scoped install for skills
        if phase and workflow_id.startswith("skills/"):
            from fotw.services.installer import install_skill_phased
            result = install_skill_phased(workflow_id, phase, ctx)
            if result is None:
                # No manifest — fall through to normal install
                pass
            elif result:
                console.print()
                console.print("[green]Installation complete![/green]")
                continue
            else:
                raise typer.Exit(1)

        if install_single_workflow(workflow_id, ctx):
            console.print()
            console.print("[green]Installation complete![/green]")
        else:
            raise typer.Exit(1)
