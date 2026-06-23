"""Core installation logic for workflows and personas."""

import shutil
import sys
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from fotw.models.workflow import Hook
from fotw.services.agents import AgentConfig, expand_tools, get_agent_config
from fotw.services.catalog import (
    PERSONAS_DIR,
    REPO_ROOT,
    WORKFLOWS_DIR,
    _EXTRA_AGENT_DIRS,
    _EXTRA_RULE_DIRS,
    _EXTRA_SKILL_DIRS,
)
from fotw.services.output_styles import (
    OUTPUT_STYLES_DIR,
    OutputStyleError,
    parse_spinner_verbs,
    style_name,
)
from fotw.services.persona_config import (
    RECORD_KEYS,
    read_persona_config,
    write_persona_config,
)
from fotw.services.settings_merger import (
    capture_previous,
    merge_env,
    merge_hooks,
    merge_output_style,
    merge_spinner_verbs,
    read_settings,
    remove_persona_keys,
    write_settings,
)
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
        console.print(r"  \[o]verwrite  \[s]kip  \[d]iff  \[b]ackup+overwrite  \[O]verwrite-all  \[S]kip-all  \[q]uit")
        choice = console.input(r"  Choice \[s]: ").strip().lower() or "s"

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


# ---------------------------------------------------------------------------
# Symlink helpers
# ---------------------------------------------------------------------------

def _atomic_symlink(target: Path, link_target: Path) -> None:
    """Create a symlink at target pointing to link_target, replacing any existing path."""
    tmp = target.with_suffix(target.suffix + ".__fotw_tmp")
    tmp.symlink_to(link_target)
    tmp.replace(target)


def _resolve_symlink_conflict(
    ctx: InstallContext, target: Path, link_target: Path
) -> bool:
    """Resolve a conflict when the install strategy is a symlink.

    Returns True if the symlink should be created, False to skip.
    """
    if ctx.force:
        return True

    # Already the correct symlink — skip silently.
    if target.is_symlink() and target.resolve() == link_target.resolve():
        if not ctx.quiet:
            console.print(f"  [dim]identical symlink: {target.name} (skipped)[/dim]")
        return False

    # Nothing at the target path — proceed.
    if not target.exists() and not target.is_symlink():
        return True

    # Sticky action from a prior choice this session.
    if ctx.sticky_action == ConflictAction.OVERWRITE_ALL:
        return True
    if ctx.sticky_action == ConflictAction.SKIP_ALL:
        return False

    if not _is_interactive():
        console.print(f"  [yellow]Non-interactive: skipping {target.name}[/yellow]")
        return False

    if target.is_symlink():
        current = target.resolve()
        console.print(f"\n  [yellow]Conflict:[/yellow] {target.name} is a symlink to {current}")
        console.print(f"  New target: {link_target}")
    else:
        console.print(f"\n  [yellow]Conflict:[/yellow] {target.name} exists as a regular file/directory")
        console.print(f"  Would convert to symlink → {link_target}")

    while True:
        console.print(r"  \[o]verwrite  \[s]kip  \[O]verwrite-all  \[S]kip-all  \[q]uit")
        choice = console.input(r"  Choice \[s]: ").strip().lower() or "s"
        if choice == "o":
            return True
        elif choice == "s":
            return False
        elif choice in ("oa", "overwrite-all"):
            ctx.sticky_action = ConflictAction.OVERWRITE_ALL
            return True
        elif choice in ("sa", "skip-all"):
            ctx.sticky_action = ConflictAction.SKIP_ALL
            return False
        elif choice == "q":
            raise InstallQuit()
        else:
            console.print(f"  [red]Unknown choice: {choice}[/red]")


def _install_as_symlink(
    target: Path,
    link_target: Path,
    ctx: InstallContext,
    label: str,
) -> bool:
    """Install link_target as a symlink at target. Returns True on success/skip."""
    if not _resolve_symlink_conflict(ctx, target, link_target):
        if not ctx.quiet:
            console.print(f"  Skipped {label}")
        return True  # skip is not failure

    if ctx.dry_run:
        if not ctx.quiet:
            console.print(f"  [yellow][DRY RUN] Would symlink:[/yellow] {target} → {link_target}")
        return True

    target.parent.mkdir(parents=True, exist_ok=True)

    # Remove any existing path safely — never rmtree through a symlink.
    if target.is_symlink() or target.is_file():
        target.unlink()
    elif target.is_dir():
        shutil.rmtree(target)

    _atomic_symlink(target, link_target)

    if not ctx.quiet:
        console.print(f"[green]\u2713[/green] Symlinked {label} \u2192 {link_target}")
    return True


# ---------------------------------------------------------------------------
# Tool directory resolution
# ---------------------------------------------------------------------------

def _get_agent_cfg(ctx: InstallContext) -> AgentConfig:
    """Look up agent config for the context's tool, with fallback."""
    cfg = get_agent_config(ctx.tool)
    if cfg is None:
        # Shouldn't happen — validated at command layer
        raise ValueError(f"Unknown tool: {ctx.tool}")
    return cfg


def _base_dir(ctx: InstallContext) -> Path:
    """Return the base tool directory (e.g., .claude/, .cursor/, .github/)."""
    cfg = _get_agent_cfg(ctx)
    if ctx.is_global:
        return Path.home() / cfg.config_dir
    return ctx.target_repo / cfg.config_dir


def _target_dir_for_type(ctx: InstallContext, wtype: str) -> Path:
    cfg = _get_agent_cfg(ctx)
    base = _base_dir(ctx)
    if wtype == "rules":
        return base / cfg.rules_subdir
    elif wtype in ("skills", "languages", "platforms", "vendors"):
        return base / cfg.skills_subdir
    elif wtype == "agents":
        return base / cfg.agents_subdir
    raise ValueError(f"Unknown workflow type: {wtype}")


# ---------------------------------------------------------------------------
# Single workflow install
# ---------------------------------------------------------------------------

def _find_source(wtype: str, name: str) -> Path | None:
    """Find the source file/directory for a workflow."""
    if wtype == "rules":
        # Check core rules first
        for ext in (".mdc", ".md"):
            p = WORKFLOWS_DIR / "rules" / f"{name}{ext}"
            if p.is_file():
                return p
        # Then language/platform/vendor rule dirs
        for extra_dir, _ in _EXTRA_RULE_DIRS:
            for ext in (".mdc", ".md"):
                p = extra_dir / f"{name}{ext}"
                if p.is_file():
                    return p
    elif wtype in ("skills", "languages", "platforms", "vendors"):
        # Check core skills first
        skill_dir = WORKFLOWS_DIR / "skills" / name
        if skill_dir.is_dir():
            return skill_dir
        # Then language/platform/vendor skill dirs
        for extra_dir, _ in _EXTRA_SKILL_DIRS:
            p = extra_dir / name
            if p.is_dir():
                return p
    elif wtype == "agents":
        agent = WORKFLOWS_DIR / "agents" / f"{name}.md"
        if agent.is_file():
            return agent
        # Then platform/vendor agent dirs
        for extra_dir, _ in _EXTRA_AGENT_DIRS:
            p = extra_dir / f"{name}.md"
            if p.is_file():
                return p
    return None


def _target_filename(source: Path, wtype: str, cfg: AgentConfig) -> str:
    """Determine the target filename, handling extension translation."""
    if wtype == "rules":
        return source.stem + cfg.rule_extension
    return source.name


def _needs_translation(wtype: str, cfg: AgentConfig) -> bool:
    """Check if the file needs frontmatter translation."""
    return wtype == "rules" and cfg.frontmatter_format != "cursor"


_TIER_DIRS = {"languages", "platforms", "vendors", "teams"}


def install_single_workflow(
    wf_id: str, ctx: InstallContext
) -> bool:
    """Install a single workflow. Returns True on success."""
    parts = wf_id.split("/")

    if len(parts) == 3 and parts[0] in _TIER_DIRS:
        # New-style: languages/skills/go-patterns, platforms/rules/cloudformation-conventions
        _tier_dir, wtype, name = parts
        install_as = wtype  # "skills", "rules", or "agents"
        base = REPO_ROOT / wf_id
        if wtype == "rules":
            # Rules have extensions: try .mdc then .md
            source: Path | None = next(
                (p for ext in (".mdc", ".md") if (p := base.parent / f"{base.name}{ext}").is_file()),
                None,
            )
        elif wtype == "agents":
            # Agents have .md extension
            candidate = base.parent / f"{base.name}.md"
            source = candidate if candidate.is_file() else None
        else:
            # Skills are directories
            source = base if base.exists() else None
    elif len(parts) == 2:
        wtype, name = parts
        install_as = wtype
        source = _find_source(wtype, name)
    else:
        err_console.print(f"[red]Error: Invalid workflow ID: {wf_id}[/red]")
        return False
    if source is None:
        if not ctx.quiet:
            err_console.print(f"[red]Error: {wtype[:-1].title()} not found: {name}[/red]")
        return False

    cfg = _get_agent_cfg(ctx)

    # Check if this workflow type is supported by the target agent
    if install_as == "agents" and not cfg.supports_agents:
        if not ctx.quiet:
            console.print(f"  [dim]Skipped {wf_id} ({cfg.name} does not support agents)[/dim]")
        return True

    if install_as == "skills" and not cfg.supports_skills:
        if not ctx.quiet:
            console.print(f"  [dim]Skipped {wf_id} ({cfg.name} does not support skills)[/dim]")
        return True

    target_dir = _target_dir_for_type(ctx, install_as)
    is_dir = source.is_dir()

    if is_dir:
        target_path = target_dir / name
    else:
        target_name = _target_filename(source, install_as, cfg)
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
        if _needs_translation(install_as, cfg):
            console.print(f"Note:     Frontmatter will be translated and cached for {cfg.name}")
        console.print()

    # Directory install (skills) — symlink the whole directory.
    if is_dir:
        return _install_as_symlink(target_path, source, ctx, f"{name}/")

    # File install (rules, agents).
    if _needs_translation(install_as, cfg):
        # Translate to cache, then symlink from target to cache.
        from fotw.services.cache import build_cache_file
        cache_path = build_cache_file(source, install_as, cfg)
        return _install_as_symlink(target_path, cache_path, ctx, source.name)
    else:
        # Direct symlink to repo source.
        return _install_as_symlink(target_path, source, ctx, source.name)


# ---------------------------------------------------------------------------
# Personas install
# ---------------------------------------------------------------------------

def install_personas(ctx: InstallContext) -> bool:
    """Install persona files to the target."""
    personas_source = PERSONAS_DIR
    config_source = PERSONAS_DIR / "_persona-config-example.yaml"

    if not personas_source.is_dir():
        if not ctx.quiet:
            err_console.print("[red]Error: Personas directory not found[/red]")
        return False

    base = _base_dir(ctx)
    persona_target = base / "personas"
    config_target = base / "persona.yaml"

    if not ctx.quiet:
        console.print()
        console.print("Personas: personas/")
        console.print(f"Tool:     {ctx.tool}")
        scope = f"Global ({base}/)" if ctx.is_global else f"Project ({ctx.target_repo})"
        console.print(f"Scope:    {scope}")
        console.print(f"Target:   {persona_target}/")
        console.print()

    if ctx.dry_run:
        if not ctx.quiet:
            console.print("[yellow][DRY RUN] Would symlink:[/yellow]")
            console.print(f"  {personas_source}/*.md -> {persona_target}/")
            for pfile in sorted(personas_source.glob("*.md")):
                if pfile.name == "_template.md":
                    continue
                console.print(f"    {pfile.name}")
            console.print(f"  {config_source} -> {config_target}")
            if ctx.tool == "claude-code":
                _preview_persona_styles(ctx, base, config_target)
        return True

    # Symlink persona files — each file is a direct symlink to the repo source.
    persona_target.mkdir(parents=True, exist_ok=True)
    count = 0
    for pfile in sorted(personas_source.glob("*.md")):
        if pfile.name == "_template.md":
            continue
        link = persona_target / pfile.name
        if link.is_symlink() and link.resolve() == pfile.resolve():
            count += 1
            continue
        if link.is_symlink() or link.is_file():
            link.unlink()
        _atomic_symlink(link, pfile)
        count += 1

    if not ctx.quiet:
        console.print(f"[green]\u2713[/green] Symlinked {count} personas to {persona_target}/")

    # Config
    config_preexisted = config_target.exists()
    if not config_preexisted:
        shutil.copy2(config_source, config_target)
        if not ctx.quiet:
            console.print(f"[green]\u2713[/green] Created default persona config: {config_target}")
    elif not ctx.quiet:
        console.print(f"[yellow]![/yellow] Persona config already exists: {config_target} (skipped)")

    # Claude Code only: output styles + settings activation
    if ctx.tool == "claude-code":
        _install_persona_styles(ctx, base)
        if config_preexisted:
            # The user already chose a persona \u2014 activate its style + spinner
            # verbs. A config created by this install never activates anything.
            _activate_persona_settings(ctx, base, config_target)

    return True


def _home_claude_dir() -> Path:
    """The global ~/.claude directory. Isolated as a seam for tests."""
    return Path.home() / ".claude"


def _fotw_plugin_enabled(base: Path) -> bool:
    """Detect an enabled fotw plugin via enabledPlugins in settings files."""
    for settings_file in ("settings.json", "settings.local.json"):
        enabled = read_settings(base / settings_file).get("enabledPlugins", {})
        if not isinstance(enabled, dict):
            continue
        for key, value in enabled.items():
            if value and (key == "fotw" or key.startswith("fotw@")):
                return True
    return False


def _fotw_plugin_active(ctx: InstallContext, base: Path) -> bool:
    """True if the fotw plugin (which already ships the styles) is enabled for
    this install. Checks the target config and, for project installs, the
    global ~/.claude config \u2014 a globally enabled plugin ships styles into
    every project."""
    if _fotw_plugin_enabled(base):
        return True
    if not ctx.is_global:
        home = _home_claude_dir()
        if home != base:
            return _fotw_plugin_enabled(home)
    return False


def _install_persona_styles(ctx: InstallContext, base: Path) -> None:
    """Symlink generated persona output styles into <base>/output-styles/.

    Skipped when the fotw plugin is enabled \u2014 the plugin already ships the
    same styles, and duplicate names would collide in the /config picker.
    """
    if _fotw_plugin_active(ctx, base):
        if not ctx.quiet:
            console.print(
                "[yellow]![/yellow] fotw plugin enabled \u2014 skipping output-style install (plugin ships them)"
            )
        return

    styles_dir = base / "output-styles"
    styles_dir.mkdir(parents=True, exist_ok=True)
    count = 0
    for style in sorted(OUTPUT_STYLES_DIR.glob("persona-*.md")):
        link = styles_dir / style.name
        if link.is_symlink() and link.resolve() == style.resolve():
            count += 1
            continue
        if link.is_symlink() or link.is_file():
            link.unlink()
        _atomic_symlink(link, style)
        count += 1
    if not ctx.quiet:
        console.print(f"[green]\u2713[/green] Symlinked {count} persona output styles to {styles_dir}/")


def _persona_settings_path(ctx: InstallContext, base: Path) -> Path:
    """Settings file persona keys live in: user settings for global installs,
    project-local settings otherwise (matching the /config picker's target)."""
    return base / ("settings.json" if ctx.is_global else "settings.local.json")


def _backup_settings(path: Path) -> None:
    if path.is_file():
        shutil.copy2(path, path.with_suffix(path.suffix + ".bak"))


def _ensure_gitignored(ctx: InstallContext, base: Path, settings_path: Path) -> None:
    """Claude Code git-ignores settings.local.json only when it creates the
    file itself; mirror that when fotw creates it."""
    if ctx.is_global:
        return
    entry = f"{base.name}/{settings_path.name}"
    gitignore = ctx.target_repo / ".gitignore"
    existing = gitignore.read_text() if gitignore.is_file() else ""
    if entry in existing.splitlines():
        return
    prefix = "" if not existing or existing.endswith("\n") else "\n"
    with gitignore.open("a") as fh:
        fh.write(f"{prefix}{entry}\n")


def _activate_persona_settings(ctx: InstallContext, base: Path, config_target: Path) -> None:
    """Write outputStyle + spinnerVerbs for the persona configured in
    persona.yaml, recording the user's previous values for restore."""
    config = read_persona_config(config_target)
    persona = config.get("persona")
    if not persona or persona == "off" or config.get("intensity") == "off":
        return
    persona_path = PERSONAS_DIR / f"{persona}.md"
    if not persona_path.is_file():
        if not ctx.quiet:
            console.print(f"[yellow]![/yellow] Unknown persona in config: {persona} (settings unchanged)")
        return
    try:
        name = style_name(persona_path)
        verbs = parse_spinner_verbs(persona_path)
    except OutputStyleError as exc:
        if not ctx.quiet:
            console.print(f"[yellow]![/yellow] {exc} (settings unchanged)")
        return

    settings_path = _persona_settings_path(ctx, base)
    settings_existed = settings_path.is_file()
    settings = read_settings(settings_path)

    record = {key: config[key] for key in RECORD_KEYS if key in config}
    record = capture_previous(settings, record)

    settings = merge_output_style(settings, name)
    settings = merge_spinner_verbs(settings, verbs)
    _backup_settings(settings_path)
    write_settings(settings, settings_path)
    if not settings_existed:
        _ensure_gitignored(ctx, base, settings_path)

    config.update(record)
    write_persona_config(config_target, config)
    if not ctx.quiet:
        console.print(
            f"[green]\u2713[/green] Activated '{name}' + spinner verbs in {settings_path} (takes effect after /clear)"
        )


def _preview_persona_styles(ctx: InstallContext, base: Path, config_target: Path) -> None:
    """Dry-run preview of the Claude Code-only output-style + settings writes."""
    if _fotw_plugin_active(ctx, base):
        console.print("  (fotw plugin enabled \u2014 output styles ship with the plugin, none installed)")
        return

    styles_dir = base / "output-styles"
    style_count = len(list(OUTPUT_STYLES_DIR.glob("persona-*.md")))
    console.print(f"  {OUTPUT_STYLES_DIR}/persona-*.md -> {styles_dir}/ ({style_count} styles)")

    if not config_target.exists():
        # A config created by the install never activates settings.
        return
    config = read_persona_config(config_target)
    persona = config.get("persona")
    if not persona or persona == "off" or config.get("intensity") == "off":
        return
    settings_path = _persona_settings_path(ctx, base)
    console.print(
        f"  Would set outputStyle + spinnerVerbs in {settings_path} for persona '{persona}'"
    )
    console.print(f"  Would record previous outputStyle/spinnerVerbs in {config_target}")
    if not settings_path.is_file():
        console.print(f"  Would add {base.name}/{settings_path.name} to .gitignore")


def _owned_symlink(link: Path, owner_dir: Path) -> bool:
    """True if link is a symlink resolving to a file inside owner_dir \u2014 i.e.
    an fotw-installed link, not a user's own symlink that happens to live here."""
    if not link.is_symlink():
        return False
    try:
        return owner_dir.resolve() in link.resolve().parents
    except OSError:
        return False


def uninstall_personas(ctx: InstallContext) -> bool:
    """Remove fotw-installed persona/style symlinks; restore recorded settings.

    persona.yaml stays in place (user config) minus the previous-value record.
    Only symlinks pointing into the fotw repo are removed \u2014 a user's own
    persona symlinked from elsewhere is left untouched.
    """
    base = _base_dir(ctx)

    removals = [
        (base / "personas", "*.md", PERSONAS_DIR),
        (base / "output-styles", "persona-*.md", OUTPUT_STYLES_DIR),
    ]

    config_target = base / "persona.yaml"
    config = read_persona_config(config_target)
    record = {key: config[key] for key in RECORD_KEYS if key in config}
    settings_path = _persona_settings_path(ctx, base)

    if ctx.dry_run:
        if not ctx.quiet:
            console.print("[yellow][DRY RUN] Would remove:[/yellow]")
            for directory, pattern, owner in removals:
                if not directory.is_dir():
                    continue
                owned = [p for p in sorted(directory.glob(pattern)) if _owned_symlink(p, owner)]
                for link in owned:
                    console.print(f"    {link}")
            if settings_path.is_file():
                restored = remove_persona_keys(read_settings(settings_path), record)
                if restored != read_settings(settings_path):
                    console.print(f"  Would restore persona keys in {settings_path}")
            console.print(f"  persona.yaml kept: {config_target}")
        return True

    for directory, pattern, owner in removals:
        if not directory.is_dir():
            continue
        for link in sorted(directory.glob(pattern)):
            if _owned_symlink(link, owner):
                link.unlink()
        try:
            directory.rmdir()
        except OSError:
            pass  # non-fotw files remain; leave the directory

    if settings_path.is_file():
        settings = read_settings(settings_path)
        restored = remove_persona_keys(settings, record)
        if restored != settings:
            _backup_settings(settings_path)
            write_settings(restored, settings_path)

    if config and record:
        for key in RECORD_KEYS:
            config.pop(key, None)
        write_persona_config(config_target, config)

    if not ctx.quiet:
        console.print(f"[green]\u2713[/green] Personas uninstalled from {base}/ (persona.yaml kept)")
    return True


# ---------------------------------------------------------------------------
# Phase-scoped skill install
# ---------------------------------------------------------------------------

def install_skill_phased(
    wf_id: str, phase: str, ctx: InstallContext
) -> bool | None:
    """Install a skill with only phase-relevant context files.

    Returns:
        True: success
        False: error
        None: no context-manifest found, caller should fall back to normal install
    """
    from fotw.services.context_resolver import VALID_PHASES, resolve_context

    if phase not in VALID_PHASES:
        err_console.print(f"[red]Error: Invalid phase '{phase}'. Must be one of: {', '.join(sorted(VALID_PHASES))}[/red]")
        return False

    parts = wf_id.split("/", 1)
    if len(parts) != 2 or parts[0] != "skills":
        err_console.print(f"[red]Error: --phase only works with skills, got: {wf_id}[/red]")
        return False

    skill_name = parts[1]
    skill_dir = WORKFLOWS_DIR / "skills" / skill_name
    if not skill_dir.is_dir():
        err_console.print(f"[red]Error: Skill not found: {skill_name}[/red]")
        return False

    files = resolve_context(skill_dir, phase=phase)

    # Check if there's actually a manifest — if resolve_context returned all files,
    # that means no manifest exists
    import frontmatter as fm
    skill_file = skill_dir / "SKILL.md"
    post = fm.load(str(skill_file))
    if post.metadata.get("context-manifest") is None:
        if not ctx.quiet:
            console.print(f"[yellow]No context-manifest in {skill_name} — installing full skill.[/yellow]")
        return None  # Signal: fall through to normal install

    if not files:
        err_console.print(f"[yellow]No files resolved for {skill_name} ({phase} phase)[/yellow]")
        return None

    cfg = _get_agent_cfg(ctx)
    target_dir = _target_dir_for_type(ctx, "skills")
    target_skill = target_dir / skill_name

    if not ctx.quiet:
        console.print()
        console.print(f"Skill:    {skill_name} ({phase} phase)")
        console.print(f"Tool:     {ctx.tool}")
        scope = "Global" if ctx.is_global else f"Project ({ctx.target_repo})"
        console.print(f"Scope:    {scope}")
        console.print(f"Files:    {len(files)}")
        console.print()

    if ctx.dry_run:
        console.print("[yellow][DRY RUN] Would copy:[/yellow]")
        for f in files:
            rel = f.relative_to(skill_dir)
            console.print(f"  {rel}")
        return True

    target_skill.mkdir(parents=True, exist_ok=True)
    for src_file in files:
        rel = src_file.relative_to(skill_dir)
        dst = target_skill / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src_file, dst)

    if not ctx.quiet:
        console.print(f"[green]\u2713[/green] Installed {skill_name} ({phase} phase): {len(files)} files")
    return True


# ---------------------------------------------------------------------------
# Starter install
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Hooks install
# ---------------------------------------------------------------------------

def install_single_hook(
    hook: Hook, ctx: InstallContext, include_tests: bool = False
) -> bool:
    """Install a single hook script. Returns True on success."""
    target_dir = Path.home() / ".claude" / "hooks"
    target = target_dir / f"{hook.name}.js"

    if not ctx.quiet:
        console.print(f"  [yellow]\u2192[/yellow] {hook.name}.js ({hook.event}:{hook.matcher or '*'})", highlight=False)

    if ctx.dry_run:
        if not ctx.quiet:
            console.print(f"    [yellow][DRY RUN] Would symlink {target} \u2192 {hook.path}[/yellow]")
        return True

    target_dir.mkdir(parents=True, exist_ok=True)
    if not _install_as_symlink(target, hook.path, ctx, f"{hook.name}.js"):
        return True  # skip is not failure
    if not ctx.quiet:
        console.print(f"    [green]\u2713[/green] Symlinked {hook.name}.js")

    # Optionally copy tests
    if include_tests and hook.has_tests:
        tests_source = hook.path.parent / "tests"
        tests_target = target_dir / "tests"
        test_file = f"{hook.name}.test.js"
        for sub in tests_source.iterdir():
            if sub.is_dir():
                test_path = sub / test_file
                if test_path.is_file():
                    dest_dir = tests_target / sub.name
                    dest_dir.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(test_path, dest_dir / test_file)
                    if not ctx.quiet:
                        console.print(f"    [green]\u2713[/green] Copied test: {sub.name}/{test_file}")

    return True


def install_hooks(ctx: InstallContext, include_tests: bool = False) -> bool:
    """Install all hooks (global + claude-code only)."""
    from fotw.services.catalog import scan_hooks

    if ctx.tool != "claude-code":
        err_console.print("[red]Error: Hooks are only supported for claude-code[/red]")
        return False

    if not ctx.is_global:
        err_console.print("[red]Error: Hooks must be installed globally (--global)[/red]")
        return False

    hooks = scan_hooks()
    if not hooks:
        if not ctx.quiet:
            console.print("[yellow]No hooks found[/yellow]")
        return True

    if not ctx.quiet:
        console.print()
        console.print("Installing hooks...")
        console.print(f"Tool:   claude-code")
        console.print(f"Scope:  Global (~/.claude/hooks/)")
        console.print()

    # Install script files
    for hook in hooks:
        install_single_hook(hook, ctx, include_tests)

    # Merge into settings.json
    settings_path = Path.home() / ".claude" / "settings.json"

    if ctx.dry_run:
        if not ctx.quiet:
            console.print()
            console.print(f"[yellow][DRY RUN] Would merge hooks config into {settings_path}[/yellow]")
        return True

    # Backup existing settings
    if settings_path.is_file():
        backup = settings_path.with_suffix(".json.bak")
        shutil.copy2(settings_path, backup)
        if not ctx.quiet:
            console.print()
            console.print(f"[cyan]Backed up settings to {backup.name}[/cyan]")

    existing = read_settings(settings_path)
    merged = merge_hooks(existing, hooks)
    write_settings(merged, settings_path)

    if not ctx.quiet:
        console.print(f"[green]\u2713[/green] Merged {len(hooks)} hooks into {settings_path}")

    # Summary
    if not ctx.quiet:
        console.print()
        console.print(f"[green]Installed {len(hooks)} hooks[/green]")

    return True


# ---------------------------------------------------------------------------
# Agent Teams install
# ---------------------------------------------------------------------------

def install_teams(ctx: InstallContext) -> bool:
    """Install Agent Teams bundle (claude-code only, global only)."""
    teams_dir = REPO_ROOT / "teams"
    if not teams_dir.is_dir():
        err_console.print("[red]Error: teams/ directory not found[/red]")
        return False

    base = Path.home() / ".claude"
    settings_path = base / "settings.json"

    if not ctx.quiet:
        console.print()
        console.print("Installing Agent Teams...")
        console.print("Tool:   claude-code")
        console.print(f"Scope:  Global ({base}/)")
        console.print()

    if ctx.dry_run:
        console.print("[yellow][DRY RUN] Would install:[/yellow]")
        console.print(f"  Skill:   teams/skills/team/ → {base / 'skills' / 'team'}/")
        console.print(f"  Agent:   teams/agents/team-lead.md → {base / 'agents' / 'team-lead.md'}")
        console.print(f"  Rule:    teams/rules/team-conventions.md → {base / 'rules' / 'team-conventions.md'}")
        hooks_dir = teams_dir / "hooks"
        if hooks_dir.is_dir():
            for hook_file in sorted(hooks_dir.glob("*.js")):
                console.print(f"  Hook:    {hook_file.name} → {base / 'hooks' / hook_file.name}")
        console.print(f"  Rosters: teams/rosters/ → {base / 'teams' / 'rosters'}/")
        console.print(f"  Env:     CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1 → {settings_path}")
        return True

    succeeded = []
    failed = []

    # 1. Skill directory
    skill_source = teams_dir / "skills" / "team"
    skill_target = base / "skills" / "team"
    if _install_as_symlink(skill_target, skill_source, ctx, "teams/skills/team/"):
        succeeded.append("skill: team")
    else:
        failed.append("skill: team")

    # 2. Agent
    agent_source = teams_dir / "agents" / "team-lead.md"
    agent_target = base / "agents" / "team-lead.md"
    if _install_as_symlink(agent_target, agent_source, ctx, "team-lead.md"):
        succeeded.append("agent: team-lead")
    else:
        failed.append("agent: team-lead")

    # 3. Rule
    rule_source = teams_dir / "rules" / "team-conventions.md"
    rule_target = base / "rules" / "team-conventions.md"
    if _install_as_symlink(rule_target, rule_source, ctx, "team-conventions.md"):
        succeeded.append("rule: team-conventions")
    else:
        failed.append("rule: team-conventions")

    # 4. Hooks — symlink scripts
    from fotw.services.catalog import scan_team_hooks
    team_hooks = scan_team_hooks()
    for hook in team_hooks:
        hook_target = base / "hooks" / f"{hook.name}.js"
        if _install_as_symlink(hook_target, hook.path, ctx, f"{hook.name}.js"):
            succeeded.append(f"hook: {hook.name}")
        else:
            failed.append(f"hook: {hook.name}")

    # 5. Merge hooks + env var into settings.json (single read-modify-write)
    if settings_path.is_file():
        backup = settings_path.with_suffix(".json.bak")
        shutil.copy2(settings_path, backup)
        if not ctx.quiet:
            console.print(f"[cyan]Backed up settings to {backup.name}[/cyan]")

    settings = read_settings(settings_path)
    if team_hooks:
        settings = merge_hooks(settings, team_hooks)
    settings = merge_env(settings, {"CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"})
    write_settings(settings, settings_path)
    if not ctx.quiet:
        if team_hooks:
            console.print(f"[green]\u2713[/green] Merged {len(team_hooks)} hook(s) into settings.json")
        console.print(f"[green]\u2713[/green] Enabled CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS in settings.json")

    # 6. Symlink rosters
    rosters_source = teams_dir / "rosters"
    rosters_target = base / "teams" / "rosters"
    rosters_target.mkdir(parents=True, exist_ok=True)
    roster_count = 0
    for roster_file in sorted(rosters_source.glob("*.yaml")):
        dest = rosters_target / roster_file.name
        if _install_as_symlink(dest, roster_file, ctx, roster_file.name):
            roster_count += 1
    roster_readme = rosters_source / "README.md"
    if roster_readme.is_file():
        _install_as_symlink(rosters_target / "README.md", roster_readme, ctx, "rosters/README.md")
    if not ctx.quiet:
        console.print(f"[green]\u2713[/green] Installed {roster_count} roster(s) to {rosters_target}/")

    # Summary
    if not ctx.quiet:
        console.print()
        console.print(f"[green]Agent Teams installed: {len(succeeded)} components[/green]")
        if failed:
            console.print(f"[red]Failed: {', '.join(failed)}[/red]")

    return len(failed) == 0


# ---------------------------------------------------------------------------
# Install all
# ---------------------------------------------------------------------------

def install_filtered(workflows: list, ctx: InstallContext) -> bool:
    """Install a pre-filtered list of workflows. Returns True if all succeed."""
    if not workflows:
        return True

    if not ctx.quiet:
        console.print()
        console.print(f"Installing {len(workflows)} matching workflow(s)...")
        console.print(f"Tool: {ctx.tool}")
        scope = "Global" if ctx.is_global else f"Project ({ctx.target_repo})"
        console.print(f"Scope: {scope}")
        console.print()

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
        ctx.sticky_action = wf_ctx.sticky_action

    if not ctx.quiet:
        console.print()
        console.print(f"[green]Installed {len(ctx.succeeded)} workflow(s)[/green]")
        if ctx.failed:
            console.print(f"[red]Failed: {', '.join(ctx.failed)}[/red]")

    return len(ctx.failed) == 0


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

    # Hooks (claude-code + global only)
    if ctx.tool == "claude-code" and ctx.is_global:
        if not ctx.quiet:
            console.print("[yellow]\u2192[/yellow] Installing hooks...")
        hook_ctx = InstallContext(
            tool=ctx.tool,
            target_repo=ctx.target_repo,
            is_global=True,
            dry_run=ctx.dry_run,
            force=ctx.force,
            quiet=True,
        )
        if install_hooks(hook_ctx):
            ctx.succeeded.append("hooks")
            if not ctx.quiet:
                console.print(f"  [green]\u2713[/green] Done")
        else:
            ctx.failed.append("hooks")
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
