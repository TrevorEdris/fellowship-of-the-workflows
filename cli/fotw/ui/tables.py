"""Rich table formatting for workflow listings."""

from rich.table import Table

from fotw.models.workflow import Persona, Starter, Workflow, WorkflowType
from fotw.ui.console import console


def _truncate(text: str, max_len: int = 50) -> str:
    if len(text) > max_len:
        return text[: max_len - 3] + "..."
    return text


def print_workflows(
    workflows: list[Workflow],
    starters: list[Starter],
    personas: list[Persona],
    type_filter: str | None = None,
) -> None:
    """Print workflows in Rich tables."""
    console.print()
    console.print("[bold]Available Workflows[/bold]")
    console.print("=" * 40)
    console.print()
    console.print(
        "[cyan]Install workflows:[/cyan] ./bin/install <workflow-id> <target-repo> --for <cursor|claude-code>"
    )
    console.print(
        "[cyan]Install starters:[/cyan]  ./bin/install starters/<tier> <target-repo> --for <cursor|claude-code|both>"
    )
    console.print()

    # Starters
    if not type_filter or type_filter == "starter":
        if starters:
            table = Table(title="starters", title_style="bold", show_header=False, box=None, padding=(0, 2))
            table.add_column("ID", style="green", min_width=30)
            table.add_column("Description")
            for s in starters:
                table.add_row(f"starters/{s.tier}", s.description)
            console.print(table)
            console.print()

    # Personas
    if not type_filter or type_filter == "persona":
        if personas:
            table = Table(title="personas", title_style="bold", show_header=False, box=None, padding=(0, 2))
            table.add_column("Name", style="cyan", min_width=20)
            table.add_column("Tagline")
            for p in personas:
                table.add_row(p.name, _truncate(p.tagline))
            console.print(table)
            console.print()
            console.print("  [cyan]Enable via:[/cyan] .claude/persona.yaml or .cursor/persona.yaml")
            console.print()

    # Group workflows by type
    type_groups: dict[WorkflowType, list[Workflow]] = {}
    for wf in workflows:
        type_groups.setdefault(wf.wtype, []).append(wf)

    # Rules
    if not type_filter or type_filter == "rule":
        rules = type_groups.get(WorkflowType.RULE, [])
        if rules:
            table = Table(title="rules", title_style="bold", show_header=False, box=None, padding=(0, 2))
            table.add_column("ID", style="green", min_width=30)
            table.add_column("Description")
            for wf in rules:
                table.add_row(wf.workflow_id, _truncate(wf.description))
            console.print(table)
            console.print()

    # Skills
    if not type_filter or type_filter == "skill":
        skills = type_groups.get(WorkflowType.SKILL, [])
        if skills:
            table = Table(title="skills", title_style="bold", show_header=False, box=None, padding=(0, 2))
            table.add_column("ID", style="green", min_width=30)
            table.add_column("Description")
            for wf in skills:
                table.add_row(wf.workflow_id, _truncate(wf.description))
            console.print(table)
            console.print()

    # Agents
    if not type_filter or type_filter == "agent":
        agents = type_groups.get(WorkflowType.AGENT, [])
        if agents:
            table = Table(title="agents", title_style="bold", show_header=False, box=None, padding=(0, 2))
            table.add_column("ID", style="green", min_width=30)
            table.add_column("Description")
            for wf in agents:
                table.add_row(wf.workflow_id, _truncate(wf.description))
            console.print(table)
            console.print()
