"""List available workflows."""

import json
from typing import Optional

import typer

from fotw.models.workflow import VALID_TAGS, _PLURAL_MAP
from fotw.services.catalog import scan_all, scan_hooks, scan_personas, scan_starters
from fotw.ui.console import console, err_console
from fotw.ui.tables import print_workflows

VALID_TYPES = ("rule", "skill", "agent", "starter", "persona", "hook")


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

    workflows = scan_all()
    starters = scan_starters()
    personas = scan_personas()
    hooks = scan_hooks()

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
        console.print_json(json.dumps(data))
        return

    # Filter by type
    if type_filter:
        show_workflows = type_filter in ("rule", "skill", "agent")
        show_starters = type_filter == "starter"
        show_personas = type_filter == "persona"
        show_hooks = type_filter == "hook"

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

    print_workflows(workflows, starters, personas, hooks, type_filter)
