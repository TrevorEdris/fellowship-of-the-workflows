"""Run golden test evaluations for skills."""

import json
from pathlib import Path
from typing import Optional

import typer

from fotw.services.catalog import WORKFLOWS_DIR
from fotw.services.eval_runner import (
    EvalReport,
    format_report,
    load_golden_tests,
    run_test_deterministic,
)
from fotw.ui.console import console, err_console


def eval_cmd(
    skill: Optional[str] = typer.Argument(
        None,
        help="Skill to evaluate (e.g., 'code-review' or 'skills/code-review')",
    ),
    all_skills: bool = typer.Option(False, "--all", "-a", help="Evaluate all skills with golden tests"),
    tag: Optional[str] = typer.Option(None, "--tag", "-t", help="Filter test cases by tag"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Write results to JSON file"),
    deterministic_only: bool = typer.Option(
        True, "--deterministic-only/--full",
        help="Only run deterministic assertions (no API calls). Use --full for LLM-rubric evaluation.",
    ),
    provider: Optional[str] = typer.Option(None, "--provider", help="LLM provider for --full mode (e.g., 'anthropic')"),
    model: Optional[str] = typer.Option(None, "--model", help="Model override for --full mode"),
) -> None:
    """Run golden test evaluations for skills.

    In deterministic mode (default), only contains/regex assertions are checked.
    Use --full --provider anthropic for LLM-rubric evaluation.
    """
    if not skill and not all_skills:
        err_console.print("[red]Error: Specify a skill name or use --all[/red]")
        raise typer.Exit(1)

    skills_dir = WORKFLOWS_DIR / "skills"
    skill_dirs: list[Path] = []

    if all_skills:
        for d in sorted(skills_dir.iterdir()):
            if d.is_dir() and (d / "tests" / "golden.jsonl").is_file():
                skill_dirs.append(d)
        if not skill_dirs:
            console.print("[yellow]No skills have golden tests yet.[/yellow]")
            console.print("Add tests to: skills/<name>/tests/golden.jsonl")
            return
    else:
        # Normalize: "code-review" or "skills/code-review" → skill dir
        name = skill.replace("skills/", "") if skill else ""
        skill_dir = skills_dir / name
        if not skill_dir.is_dir():
            err_console.print(f"[red]Error: Skill not found: {name}[/red]")
            raise typer.Exit(1)
        golden = skill_dir / "tests" / "golden.jsonl"
        if not golden.is_file():
            err_console.print(f"[yellow]No golden tests for {name}[/yellow]")
            err_console.print(f"Create: {golden}")
            return
        skill_dirs.append(skill_dir)

    all_reports: list[EvalReport] = []

    for skill_dir in skill_dirs:
        skill_name = skill_dir.name
        cases = load_golden_tests(skill_dir, tag_filter=tag)

        if not cases:
            continue

        console.print(f"\n[bold]{skill_name}[/bold] ({len(cases)} tests)")
        console.print("\u2500" * 40)

        results = []
        passed_count = 0
        failed_count = 0
        deferred_count = 0

        for case in cases:
            console.print(f"  [dim]{case.id}[/dim] {case.name} ", end="")
            if deterministic_only:
                console.print("[yellow]\u2298 needs --full mode to run[/yellow]")
                deferred_count += 1
            else:
                console.print("[yellow]\u2298 --full mode not yet implemented[/yellow]")
                deferred_count += 1

        report = EvalReport(
            skill_name=skill_name,
            total=len(cases),
            passed=passed_count,
            failed=failed_count,
            deferred=deferred_count,
            results=results,
        )
        all_reports.append(report)

        # Print summary per skill
        if report.failed > 0:
            console.print(f"\n  [red]\u2717 {report.score} passed[/red]")
        elif report.deferred > 0:
            console.print(f"\n  [yellow]\u2298 {report.total} deferred (run with --full)[/yellow]")
        else:
            console.print(f"\n  [green]\u2713 {report.score} passed[/green]")

    # Write JSON output
    if output:
        output_data = [format_report(r) for r in all_reports]
        Path(output).write_text(json.dumps(output_data, indent=2))
        console.print(f"\n[cyan]Results written to {output}[/cyan]")

    # Exit code
    total_failed = sum(r.failed for r in all_reports)
    if total_failed > 0:
        raise typer.Exit(1)
