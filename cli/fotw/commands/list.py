"""List available workflows."""

import json
from typing import Optional

import typer

from fotw.models.workflow import VALID_TAGS, _PLURAL_MAP
from fotw.services.catalog import scan_all, scan_hooks, scan_personas, scan_roles, scan_starters
from fotw.ui.console import console, err_console
from fotw.ui.tables import print_workflows

VALID_TYPES = ("rule", "skill", "agent", "starter", "persona", "hook", "role")


def _normalize_type(value: str) -> str:
    """Normalize plural to singular."""
    return _PLURAL_MAP.get(value, value)


def list_cmd(
    type_: Optional[str] = typer.Option(
        None, "--type", "-T", help="Filter by type (rule, skill, agent, starter, persona, hook)"
    ),
    tag: Optional[str] = typer.Option(
        None, "--tag", "-t", help="Filter skills by tag (e.g., aws, infrastructure, review)"
    ),
    as_json: bool = typer.Option(False, "--json", help="Output as JSON"),
    context_budget: bool = typer.Option(False, "--context-budget", help="Show estimated token budget per skill"),
) -> None:
    """List available workflows, starters, and hooks."""
    type_filter = None
    if type_ is not None:
        type_filter = _normalize_type(type_)
        if type_filter not in VALID_TYPES:
            err_console.print(f"[red]Unknown type: {type_}[/red]")
            err_console.print(f"Valid types: {', '.join(VALID_TYPES)}")
            raise typer.Exit(1)

    # Validate and normalize tag
    if tag:
        tag = tag.lower()
        if tag not in VALID_TAGS:
            err_console.print(f"[red]Unknown tag: {tag}[/red]")
            err_console.print(f"Valid tags: {', '.join(sorted(VALID_TAGS))}")
            raise typer.Exit(1)

    # --tag implies --type skill
    if tag and not type_filter:
        type_filter = "skill"

    if context_budget:
        from rich.table import Table

        from fotw.services.catalog import WORKFLOWS_DIR
        from fotw.services.context_budget import estimate_skill

        skills_dir = WORKFLOWS_DIR / "skills"
        budgets = []
        for skill_dir in sorted(skills_dir.iterdir()):
            if not skill_dir.is_dir() or not (skill_dir / "SKILL.md").is_file():
                continue
            budgets.append(estimate_skill(skill_dir))

        budgets.sort(key=lambda b: b.total_tokens, reverse=True)

        table = Table(title="Skill Context Budgets", show_header=True, box=None, padding=(0, 2))
        table.add_column("Skill", style="green", min_width=30)
        table.add_column("Files", justify="right")
        table.add_column("Tokens (est.)", justify="right", style="cyan")
        table.add_column("Chars", justify="right", style="dim")

        for b in budgets:
            token_style = "red" if b.total_tokens > 10000 else "yellow" if b.total_tokens > 5000 else "green"
            table.add_row(
                b.name,
                str(b.file_count),
                f"[{token_style}]{b.total_tokens:,}[/{token_style}]",
                f"{b.total_chars:,}",
            )

        console.print(table)
        console.print()
        console.print("[dim]Estimate: 1 token \u2248 4 chars. Red = >10K tokens, Yellow = >5K, Green = <5K[/dim]")
        return

    workflows = scan_all()
    starters = scan_starters()
    personas = scan_personas()
    hooks = scan_hooks()
    roles = scan_roles()

    # Filter by tag (skills only)
    if tag:
        workflows = [wf for wf in workflows if tag in wf.tags]

    if as_json:
        data = []
        if not type_filter or type_filter in ("rule", "skill", "agent"):
            for wf in workflows:
                if type_filter and wf.wtype.value != type_filter:
                    continue
                entry = {
                    "id": wf.workflow_id,
                    "type": wf.wtype.value,
                    "name": wf.name,
                    "description": wf.description,
                }
                if wf.tags:
                    entry["tags"] = wf.tags
                data.append(entry)
        if not type_filter or type_filter == "starter":
            for s in starters:
                data.append(
                    {
                        "id": f"starters/{s.tier}",
                        "type": "starter",
                        "name": s.tier,
                        "description": s.description,
                    }
                )
        if not type_filter or type_filter == "persona":
            for p in personas:
                data.append(
                    {
                        "id": f"personas/{p.name}",
                        "type": "persona",
                        "name": p.name,
                        "description": p.tagline,
                    }
                )
        if not type_filter or type_filter == "hook":
            for h in hooks:
                data.append(
                    {
                        "id": h.workflow_id,
                        "type": "hook",
                        "name": h.name,
                        "event": h.event,
                        "matcher": h.matcher,
                        "description": h.description,
                    }
                )
        if not type_filter or type_filter == "role":
            for r in roles:
                entry = {
                    "id": r.workflow_id,
                    "type": "role",
                    "name": r.name,
                    "description": r.description,
                }
                if r.tags:
                    entry["tags"] = r.tags
                if r.allowed_skills:
                    entry["allowed_skills"] = r.allowed_skills
                data.append(entry)
        console.print_json(json.dumps(data))
        return

    # Filter by type
    if type_filter:
        show_workflows = type_filter in ("rule", "skill", "agent")
        show_starters = type_filter == "starter"
        show_personas = type_filter == "persona"
        show_hooks = type_filter == "hook"
        show_roles = type_filter == "role"

        if show_workflows:
            workflows = [wf for wf in workflows if wf.wtype.value == type_filter]
        else:
            workflows = []
        if not show_starters:
            starters = []
        if not show_personas:
            personas = []
        if not show_hooks:
            hooks = []
        if not show_roles:
            roles = []

    print_workflows(workflows, starters, personas, hooks, roles, type_filter)
