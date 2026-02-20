"""Core installation logic for workflows, starters, and personas."""

import shutil
import sys
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from fotw.services.catalog import REPO_ROOT, STARTERS_DIR, WORKFLOWS_DIR
from fotw.services.frontmatter_translator import translate_content, translate_to_claude
from fotw.ui.console import console, err_console
from fotw.ui.diff import files_are_identical, show_diff

# ---------------------------------------------------------------------------
# Conflict resolution
# ---------------------------------------------------------------------------

class InstallQuit(Exception):
    """Raised when the user chooses to quit during conflict resolution."""


class ConflictAction(str, Enum):
    OVERWRITE = "overwrite"
    SKIP = "skip"
    DIFF = "diff"
    BACKUP = "backup"
    OVERWRITE_ALL = "overwrite_all"
    SKIP_ALL = "skip_all"
    QUIT = "quit"


@dataclass
class InstallContext:
    """Tracks state across a multi-file install session."""

    tool: str
    target_repo: Path
    is_global: bool = False
    dry_run: bool = False
    force: bool = False
    to_claude_dir: bool = False
    quiet: bool = False

    # Sticky choices from "overwrite all" / "skip all"
    sticky_action: ConflictAction | None = None

    # Counters
    succeeded: list[str] = field(default_factory=list)
    failed: list[str] = field(default_factory=list)


def _is_interactive() -> bool:
    """Check if stdin is a terminal (not piped)."""
    return sys.stdin.isatty()


def _prompt_conflict(filename: str, existing: str, new_content: str) -> ConflictAction:
    """Prompt the user for conflict resolution."""
    if not _is_interactive():
        console.print(f"  [yellow]Non-interactive: skipping {filename}[/yellow]")
        return ConflictAction.SKIP

    while True:
        console.print(f"\n  [yellow]Conflict:[/yellow] {filename} already exists")
        console.print("  [o]verwrite  [s]kip  [d]iff  [b]ackup+overwrite  [O]verwrite-all  [S]kip-all  [q]uit")
        choice = console.input("  Choice [s]: ").strip().lower() or "s"

        if choice == "o":
            return ConflictAction.OVERWRITE
        elif choice == "s":
            return ConflictAction.SKIP
        elif choice == "d":
            show_diff(existing, new_content, filename)
            # Loop to ask again after showing diff
        elif choice == "b":
            return ConflictAction.BACKUP
        elif choice in ("oa", "overwrite-all"):
            return ConflictAction.OVERWRITE_ALL
        elif choice in ("sa", "skip-all"):
            return ConflictAction.SKIP_ALL
        elif choice == "q":
            return ConflictAction.QUIT
        else:
            console.print(f"  [red]Unknown choice: {choice}[/red]")


def _resolve_conflict(
    ctx: InstallContext, target: Path, new_content: str
) -> bool:
    """Resolve a file conflict. Returns True if file should be written."""
    if ctx.force:
        return True

    if not target.exists():
        return True

    existing = target.read_text()

    # Identical file — skip silently
    if files_are_identical(existing, new_content):
        if not ctx.quiet:
            console.print(f"  [dim]identical: {target.name} (skipped)[/dim]")
        return False

    # Sticky action from previous choice
    if ctx.sticky_action == ConflictAction.OVERWRITE_ALL:
        return True
    if ctx.sticky_action == ConflictAction.SKIP_ALL:
        return False

    action = _prompt_conflict(target.name, existing, new_content)

    if action == ConflictAction.OVERWRITE:
        return True
    elif action == ConflictAction.SKIP:
        return False
    elif action == ConflictAction.BACKUP:
        backup = target.with_suffix(target.suffix + ".bak")
        shutil.copy2(target, backup)
        console.print(f"  [cyan]Backed up to {backup.name}[/cyan]")
        return True
    elif action == ConflictAction.OVERWRITE_ALL:
        ctx.sticky_action = ConflictAction.OVERWRITE_ALL
        return True
    elif action == ConflictAction.SKIP_ALL:
        ctx.sticky_action = ConflictAction.SKIP_ALL
        return False
    elif action == ConflictAction.QUIT:
        raise InstallQuit()

    return False


def _resolve_dir_conflict(ctx: InstallContext, target_dir: Path, source_dir: Path) -> bool:
    """Resolve a directory conflict. Returns True if directory should be written."""
    if ctx.force:
        return True

    if not target_dir.exists():
        return True

    if ctx.sticky_action == ConflictAction.OVERWRITE_ALL:
        return True
    if ctx.sticky_action == ConflictAction.SKIP_ALL:
        return False

    if not _is_interactive():
        console.print(f"  [yellow]Non-interactive: skipping {target_dir.name}/[/yellow]")
        return False

    console.print(f"\n  [yellow]Conflict:[/yellow] {target_dir.name}/ already exists")
    console.print("  [o]verwrite  [s]kip  [O]verwrite-all  [S]kip-all  [q]uit")
    choice = console.input("  Choice [s]: ").strip().lower() or "s"

    if choice == "o":
        return True
    elif choice in ("oa", "overwrite-all"):
        ctx.sticky_action = ConflictAction.OVERWRITE_ALL
        return True
    elif choice in ("sa", "skip-all"):
        ctx.sticky_action = ConflictAction.SKIP_ALL
        return False
    elif choice == "q":
        raise InstallQuit()
    return False


# ---------------------------------------------------------------------------
# Tool directory resolution
# ---------------------------------------------------------------------------

def _base_dir(ctx: InstallContext) -> Path:
    """Return the base tool directory (.claude/ or .cursor/)."""
    if ctx.is_global:
        home = Path.home()
        return home / ".cursor" if ctx.tool == "cursor" else home / ".claude"
    return ctx.target_repo / (".cursor" if ctx.tool == "cursor" else ".claude")


def _rules_dir(ctx: InstallContext) -> Path:
    return _base_dir(ctx) / "rules"


def _skills_dir(ctx: InstallContext) -> Path:
    return _base_dir(ctx) / "skills"


def _agents_dir(ctx: InstallContext) -> Path:
    return _base_dir(ctx) / "agents"


def _target_dir_for_type(ctx: InstallContext, wtype: str) -> Path:
    if wtype == "rules":
        return _rules_dir(ctx)
    elif wtype == "skills":
        return _skills_dir(ctx)
    elif wtype == "agents":
        return _agents_dir(ctx)
    raise ValueError(f"Unknown workflow type: {wtype}")


# ---------------------------------------------------------------------------
# Single workflow install
# ---------------------------------------------------------------------------

def _find_source(wtype: str, name: str) -> Path | None:
    """Find the source file/directory for a workflow."""
    if wtype == "rules":
        mdc = WORKFLOWS_DIR / "rules" / f"{name}.mdc"
        if mdc.is_file():
            return mdc
        md = WORKFLOWS_DIR / "rules" / f"{name}.md"
        if md.is_file():
            return md
    elif wtype == "skills":
        skill_dir = WORKFLOWS_DIR / "skills" / name
        if skill_dir.is_dir():
            return skill_dir
    elif wtype == "agents":
        agent = WORKFLOWS_DIR / "agents" / f"{name}.md"
        if agent.is_file():
            return agent
    return None


def _target_filename(source: Path, wtype: str, tool: str) -> str:
    """Determine the target filename, handling extension translation."""
    if wtype == "rules":
        if tool == "cursor":
            # Keep .mdc for Cursor
            if source.suffix == ".mdc":
                return source.name
            return source.stem + ".mdc"
        else:
            # Convert to .md for Claude
            return source.stem + ".md"
    return source.name


def _get_new_content(source: Path, wtype: str, tool: str) -> str:
    """Get the content that would be written to the target file."""
    if wtype == "rules" and tool == "claude-code":
        return translate_content(source)
    return source.read_text()


def install_single_workflow(
    wf_id: str, ctx: InstallContext
) -> bool:
    """Install a single workflow. Returns True on success."""
    parts = wf_id.split("/", 1)
    if len(parts) != 2:
        err_console.print(f"[red]Error: Invalid workflow ID: {wf_id}[/red]")
        return False

    wtype, name = parts

    source = _find_source(wtype, name)
    if source is None:
        if not ctx.quiet:
            err_console.print(f"[red]Error: {wtype[:-1].title()} not found: {name}[/red]")
        return False

    target_dir = _target_dir_for_type(ctx, wtype)
    is_dir = source.is_dir()

    if is_dir:
        target_path = target_dir / name
    else:
        target_name = _target_filename(source, wtype, ctx.tool)
        target_path = target_dir / target_name

    # Info output
    if not ctx.quiet:
        console.print()
        console.print(f"Workflow: {wf_id}")
        console.print(f"Tool:     {ctx.tool}")
        scope = "Global" if ctx.is_global else f"Project ({ctx.target_repo})"
        console.print(f"Scope:    {scope}")
        console.print(f"Source:   {source}")
        console.print(f"Target:   {target_path}")
        if wtype == "rules" and ctx.tool == "claude-code":
            console.print("Note:     Frontmatter will be translated for Claude Code")
        console.print()

    # Dry run
    if ctx.dry_run:
        if not ctx.quiet:
            console.print("[yellow][DRY RUN] Would copy:[/yellow]")
            if is_dir:
                console.print(f"  {source}/ -> {target_path}/")
                for f in sorted(source.rglob("*")):
                    if f.is_file():
                        console.print(f"    {f.relative_to(source)}")
            else:
                console.print(f"  {source} -> {target_path}")
        return True

    # Directory install (skills)
    if is_dir:
        if not _resolve_dir_conflict(ctx, target_path, source):
            if not ctx.quiet:
                console.print(f"  Skipped {wf_id}")
            return True  # Skip is not a failure

        target_dir.mkdir(parents=True, exist_ok=True)
        if target_path.exists():
            shutil.rmtree(target_path)
        shutil.copytree(source, target_path)
        if not ctx.quiet:
            console.print(f"[green]\u2713[/green] Copied skill directory to {target_path}")
        return True

    # File install (rules, agents)
    new_content = _get_new_content(source, wtype, ctx.tool)

    if not _resolve_conflict(ctx, target_path, new_content):
        if not ctx.quiet:
            console.print(f"  Skipped {wf_id}")
        return True  # Skip is not a failure

    target_dir.mkdir(parents=True, exist_ok=True)
    if wtype == "rules" and ctx.tool == "claude-code":
        translate_to_claude(source, target_path)
        if not ctx.quiet:
            console.print(f"[green]\u2713[/green] Translated and installed {source.name} -> {target_path}")
    else:
        shutil.copy2(source, target_path)
        if not ctx.quiet:
            console.print(f"[green]\u2713[/green] Installed {source.name} -> {target_path}")

    return True


# ---------------------------------------------------------------------------
# Personas install
# ---------------------------------------------------------------------------

def install_personas(ctx: InstallContext) -> bool:
    """Install persona files to the target."""
    personas_source = STARTERS_DIR / "personas"
    config_source = STARTERS_DIR / "snippets" / "persona-config-example.yaml"

    if not personas_source.is_dir():
        if not ctx.quiet:
            err_console.print("[red]Error: Personas directory not found[/red]")
        return False

    base = _base_dir(ctx)
    persona_target = base / "personas"
    config_target = base / "persona.yaml"

    if not ctx.quiet:
        console.print()
        console.print("Personas: starters/personas/")
        console.print(f"Tool:     {ctx.tool}")
        scope = f"Global ({base}/)" if ctx.is_global else f"Project ({ctx.target_repo})"
        console.print(f"Scope:    {scope}")
        console.print(f"Target:   {persona_target}/")
        console.print()

    if ctx.dry_run:
        if not ctx.quiet:
            console.print("[yellow][DRY RUN] Would copy:[/yellow]")
            console.print(f"  {personas_source}/ -> {persona_target}/")
            for pfile in sorted(personas_source.glob("*.md")):
                if pfile.name == "_template.md":
                    continue
                console.print(f"    {pfile.name}")
            console.print(f"  {config_source} -> {config_target}")
        return True

    # Copy persona files
    persona_target.mkdir(parents=True, exist_ok=True)
    count = 0
    for pfile in sorted(personas_source.glob("*.md")):
        if pfile.name == "_template.md":
            continue
        shutil.copy2(pfile, persona_target / pfile.name)
        count += 1

    if not ctx.quiet:
        console.print(f"[green]\u2713[/green] Copied {count} personas to {persona_target}/")

    # Config
    if not config_target.exists():
        shutil.copy2(config_source, config_target)
        if not ctx.quiet:
            console.print(f"[green]\u2713[/green] Created default persona config: {config_target}")
    elif not ctx.quiet:
        console.print(f"[yellow]![/yellow] Persona config already exists: {config_target} (skipped)")

    return True


# ---------------------------------------------------------------------------
# Starter install
# ---------------------------------------------------------------------------

TIER_RULES = {
    "minimal": ["git-safety", "output-style"],
    "standard": ["git-safety", "output-style", "discover-plan-implement", "ai-session"],
    "full": [
        "git-safety", "output-style", "discover-plan-implement",
        "ai-session", "multi-repo-safety", "persona-integration",
    ],
}


def install_starter(tier: str, ctx: InstallContext) -> bool:
    """Install a starter template with tier-appropriate rules."""
    # Find source
    source = STARTERS_DIR / f"{tier}.md"
    if not source.is_file():
        # Fall back to old format
        source = STARTERS_DIR / f"CLAUDE.md.{tier}"
        if not source.is_file():
            err_console.print(f"[red]Error: Unknown starter tier: {tier}[/red]")
            err_console.print("Available tiers: minimal, standard, full")
            return False

    # Determine targets based on tool
    targets: list[Path] = []
    if ctx.tool in ("claude-code", "both"):
        if ctx.to_claude_dir:
            targets.append(ctx.target_repo / ".claude" / "CLAUDE.md")
        else:
            targets.append(ctx.target_repo / "CLAUDE.md")
    if ctx.tool in ("cursor", "both"):
        targets.append(ctx.target_repo / "AGENTS.md")

    # Info
    console.print()
    console.print(f"Starter:  {tier}")
    console.print(f"Tool:     {ctx.tool}")
    console.print(f"Source:   {source}")
    for t in targets:
        console.print(f"Target:   {t}")
    console.print()

    if ctx.dry_run:
        console.print("[yellow][DRY RUN] Would copy:[/yellow]")
        for t in targets:
            console.print(f"  {source} -> {t}")
        if tier == "full":
            console.print()
            console.print("[yellow][DRY RUN] Would also install personas[/yellow]")
        rules = TIER_RULES.get(tier, [])
        if rules:
            console.print()
            console.print(f"[yellow][DRY RUN] Would bundle rules for {tier} tier: {', '.join(rules)}[/yellow]")
        return True

    # Copy starter files
    source_content = source.read_text()
    for t in targets:
        if not _resolve_conflict(ctx, t, source_content):
            continue
        t.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, t)
        console.print(f"[green]\u2713[/green] Installed {t.name}")

    # Full tier gets personas
    if tier == "full":
        # Personas for each tool target
        tools_to_install = []
        if ctx.tool in ("claude-code", "both"):
            tools_to_install.append("claude-code")
        if ctx.tool in ("cursor", "both"):
            tools_to_install.append("cursor")

        for t in tools_to_install:
            persona_ctx = InstallContext(
                tool=t,
                target_repo=ctx.target_repo,
                is_global=False,
                dry_run=ctx.dry_run,
                force=ctx.force,
                quiet=True,
            )
            install_personas(persona_ctx)

        # Show persona summary (install_personas already did the work quietly)
        persona_source = STARTERS_DIR / "personas"
        persona_count = sum(1 for p in persona_source.glob("*.md") if p.name != "_template.md")
        base = _base_dir(ctx)
        console.print(f"[green]\u2713[/green] Installed {persona_count} personas to {base / 'personas'}/")

    # Bundle tier rules
    rules = TIER_RULES.get(tier, [])
    if rules:
        console.print()
        console.print(f"Bundled rules for {tier} tier: {' '.join(rules)}")
        # Install rules for each tool target
        tools_to_install = []
        if ctx.tool in ("claude-code", "both"):
            tools_to_install.append("claude-code")
        if ctx.tool in ("cursor", "both"):
            tools_to_install.append("cursor")

        for t in tools_to_install:
            rule_ctx = InstallContext(
                tool=t,
                target_repo=ctx.target_repo,
                is_global=False,
                dry_run=ctx.dry_run,
                force=ctx.force,
                quiet=True,
                sticky_action=ctx.sticky_action,
            )
            for rule_name in rules:
                install_single_workflow(f"rules/{rule_name}", rule_ctx)

    # Next steps
    console.print()
    console.print("Next steps:")
    console.print(f"  1. Edit the starter file(s) to fill in your project details")
    console.print(f"  2. Install workflows: ./bin/install skills/code-review {ctx.target_repo} --for claude-code")
    if tier == "full":
        console.print(f"  3. Switch personas: ./bin/install skills/switch-persona {ctx.target_repo} --for claude-code")

    return True


# ---------------------------------------------------------------------------
# Install all
# ---------------------------------------------------------------------------

def install_all(ctx: InstallContext) -> bool:
    """Install all workflows and personas."""
    from fotw.services.catalog import scan_all

    console.print()
    console.print("Installing all workflows...")
    console.print(f"Tool: {ctx.tool}")
    scope = "Global" if ctx.is_global else f"Project ({ctx.target_repo})"
    console.print(f"Scope: {scope}")
    console.print()

    workflows = scan_all()
    for wf in workflows:
        wf_id = wf.workflow_id
        if not ctx.quiet:
            console.print(f"[yellow]\u2192[/yellow] Installing {wf_id}...")
        wf_ctx = InstallContext(
            tool=ctx.tool,
            target_repo=ctx.target_repo,
            is_global=ctx.is_global,
            dry_run=ctx.dry_run,
            force=ctx.force,
            quiet=True,
            sticky_action=ctx.sticky_action,
        )
        if install_single_workflow(wf_id, wf_ctx):
            ctx.succeeded.append(wf_id)
            if not ctx.quiet:
                console.print(f"  [green]\u2713[/green] Done")
        else:
            ctx.failed.append(wf_id)
            if not ctx.quiet:
                console.print(f"  [red]\u2717[/red] Failed")
        # Propagate sticky action
        ctx.sticky_action = wf_ctx.sticky_action

    # Personas
    if not ctx.quiet:
        console.print("[yellow]\u2192[/yellow] Installing personas...")
    persona_ctx = InstallContext(
        tool=ctx.tool,
        target_repo=ctx.target_repo,
        is_global=ctx.is_global,
        dry_run=ctx.dry_run,
        force=ctx.force,
        quiet=True,
    )
    if install_personas(persona_ctx):
        ctx.succeeded.append("personas")
        if not ctx.quiet:
            console.print(f"  [green]\u2713[/green] Done")
    else:
        ctx.failed.append("personas")
        if not ctx.quiet:
            console.print(f"  [red]\u2717[/red] Failed")

    # Summary
    console.print()
    console.print("\u2550" * 40)
    console.print("Installation Summary")
    console.print("\u2550" * 40)
    console.print()

    if ctx.succeeded:
        console.print(f"[green]Succeeded ({len(ctx.succeeded)}):[/green]")
        for wf in ctx.succeeded:
            console.print(f"  [green]\u2713[/green] {wf}")
        console.print()

    if ctx.failed:
        console.print(f"[red]Failed ({len(ctx.failed)}):[/red]")
        for wf in ctx.failed:
            console.print(f"  [red]\u2717[/red] {wf}")
        console.print()

    console.print(f"Total: {len(ctx.succeeded)} succeeded, {len(ctx.failed)} failed")

    return len(ctx.failed) == 0
