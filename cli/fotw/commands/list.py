"""List available workflows."""

import json
from typing import Optional

import typer

from fotw.models.workflow import _PLURAL_MAP
from fotw.services.catalog import scan_all, scan_personas, scan_starters
from fotw.ui.console import console, err_console
from fotw.ui.tables import print_workflows

VALID_TYPES = ("rule", "skill", "agent", "starter", "persona")


def _normalize_type(value: str) -> str:
    """Normalize plural to singular."""
    return _PLURAL_MAP.get(value, value)


def list_cmd(
    type_: Optional[str] = typer.Option(
        None, "--type", "-T", help="Filter by type (rule, skill, agent, starter, persona)"
    ),
    as_json: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """List available workflows and starters."""
    type_filter = None
    if type_ is not None:
        type_filter = _normalize_type(type_)
        if type_filter not in VALID_TYPES:
            err_console.print(f"[red]Unknown type: {type_}[/red]")
            err_console.print(f"Valid types: {', '.join(VALID_TYPES)}")
            raise typer.Exit(1)

    workflows = scan_all()
    starters = scan_starters()
    personas = scan_personas()

    if as_json:
        data = []
        if not type_filter or type_filter in ("rule", "skill", "agent"):
            for wf in workflows:
                if type_filter and wf.wtype.value != type_filter:
                    continue
                data.append(
                    {
                        "id": wf.workflow_id,
                        "type": wf.wtype.value,
                        "name": wf.name,
                        "description": wf.description,
                    }
                )
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
        console.print_json(json.dumps(data))
        return

    # Filter by type
    if type_filter:
        show_workflows = type_filter in ("rule", "skill", "agent")
        show_starters = type_filter == "starter"
        show_personas = type_filter == "persona"

        if show_workflows:
            workflows = [wf for wf in workflows if wf.wtype.value == type_filter]
        else:
            workflows = []
        if not show_starters:
            starters = []
        if not show_personas:
            personas = []

    print_workflows(workflows, starters, personas, type_filter)
