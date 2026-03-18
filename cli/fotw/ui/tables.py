"""Rich table formatting for workflow listings."""

from rich.table import Table

from fotw.models.workflow import Hook, Persona, Role, Starter, Workflow, WorkflowType
from fotw.ui.console import console


def _truncate(text: str, max_len: int = 50) -> str:
    if len(text) > max_len:
        return text[: max_len - 3] + "..."
    return text


def print_workflows(
    workflows: list[Workflow],
    starters: list[Starter],
    personas: list[Persona],
    hooks: list[Hook] | None = None,
    roles: list[Role] | None = None,
    type_filter: str | None = None,
) -> None:
    """Print workflows in Rich tables."""
    console.print()
    console.print("[bold]Available Workflows[/bold]")
    console.print("=" * 40)
    console.print()
    console.print(
        "[cyan]Install workflows:[/cyan] ./bin/fotw install <workflow-id> <target-repo> --for <tool>"
    )
    console.print(
        "[cyan]Install starters:[/cyan]  ./bin/fotw install starters/<tier> <target-repo> --for <tool>"
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
            console.print("  [cyan]Enable via:[/cyan] .<tool>/persona.yaml (e.g., .claude/persona.yaml)")
            console.print()

    # Group workflows by type
    type_groups: dict[WorkflowType, list[Workflow]] = {}
    for wf in workflows:
        type_groups.setdefault(wf.wtype, []).append(wf)

    # Rules
    if not type_filter or type_filter == "rule":
        rules = type_groups.get(WorkflowType.RULE, [])
        if rules:
            has_non_core = any(wf.tier != "core" for wf in rules)
            table = Table(title="rules", title_style="bold", show_header=has_non_core, box=None, padding=(0, 2))
            table.add_column("ID", style="green", min_width=30)
            if has_non_core:
                table.add_column("Tier", style="dim", min_width=12)
            table.add_column("Description")
            for wf in rules:
                row = [wf.workflow_id]
                if has_non_core:
                    tier_label = wf.tier if wf.tier != "core" else ""
                    row.append(f"[dim]{tier_label}[/dim]" if tier_label else "")
                row.append(_truncate(wf.description))
                table.add_row(*row)
            console.print(table)
            console.print()

    # Skills
    if not type_filter or type_filter == "skill":
        skills = type_groups.get(WorkflowType.SKILL, [])
        if skills:
            has_tags = any(wf.tags for wf in skills)
            has_non_core = any(wf.tier != "core" for wf in skills)
            table = Table(title="skills", title_style="bold", show_header=True, box=None, padding=(0, 2))
            table.add_column("ID", style="green", min_width=30)
            if has_non_core:
                table.add_column("Tier", style="dim", min_width=12)
            if has_tags:
                table.add_column("Tags", style="cyan", min_width=20)
            table.add_column("Description")
            for wf in skills:
                row = [wf.workflow_id]
                if has_non_core:
                    tier_label = wf.tier if wf.tier != "core" else ""
                    row.append(f"[dim]{tier_label}[/dim]" if tier_label else "")
                if has_tags:
                    row.append(", ".join(wf.tags))
                row.append(_truncate(wf.description))
                table.add_row(*row)
            console.print(table)
            console.print()

    # Agents
    if not type_filter or type_filter == "agent":
        agents = type_groups.get(WorkflowType.AGENT, [])
        if agents:
            has_non_core = any(wf.tier != "core" for wf in agents)
            table = Table(title="agents", title_style="bold", show_header=has_non_core, box=None, padding=(0, 2))
            table.add_column("ID", style="green", min_width=30)
            if has_non_core:
                table.add_column("Tier", style="dim", min_width=12)
            table.add_column("Description")
            for wf in agents:
                row = [wf.workflow_id]
                if has_non_core:
                    tier_label = wf.tier if wf.tier != "core" else ""
                    row.append(f"[dim]{tier_label}[/dim]" if tier_label else "")
                row.append(_truncate(wf.description))
                table.add_row(*row)
            console.print(table)
            console.print()

    # Hooks
    if not type_filter or type_filter == "hook":
        if hooks:
            table = Table(title="hooks", title_style="bold", show_header=True, box=None, padding=(0, 2))
            table.add_column("ID", style="green", min_width=30)
            table.add_column("Event", style="cyan")
            table.add_column("Matcher")
            table.add_column("Description")
            for h in hooks:
                table.add_row(h.workflow_id, h.event, h.matcher or "*", _truncate(h.description))
            console.print(table)
            console.print()
            console.print("  [cyan]Install hooks:[/cyan] ./bin/fotw install hooks --global --for claude-code")
            console.print()

    # Roles
    if not type_filter or type_filter == "role":
        if roles:
            table = Table(title="roles (roster)", title_style="bold", show_header=True, box=None, padding=(0, 2))
            table.add_column("ID", style="green", min_width=30)
            table.add_column("Tags", style="cyan", min_width=15)
            table.add_column("Skills", style="dim", min_width=10)
            table.add_column("Description")
            for r in roles:
                table.add_row(
                    r.workflow_id,
                    ", ".join(r.tags) if r.tags else "",
                    str(len(r.allowed_skills)),
                    _truncate(r.description),
                )
            console.print(table)
            console.print()
            console.print("  [cyan]Install role:[/cyan] ./bin/fotw install rosters/<name> <target-repo> --for <tool>")
            console.print()
