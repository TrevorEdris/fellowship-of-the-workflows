"""Validate workflow files."""

from typing import Optional

import typer
from fotw.services.catalog import validate_all
from fotw.ui.console import console, err_console


def validate_cmd(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show each file as it's validated"),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Only output errors"),
    path: Optional[str] = typer.Option(None, "--path", help="Validate a specific file or directory"),
) -> None:
    """Validate workflow files for correctness."""
    if not quiet:
        console.print("Validating workflows...")
        console.print()

    results = validate_all(target_path=path)

    errors = 0
    warnings = 0

    for result in results:
        for err in result.errors:
            err_console.print(f"[red]ERROR:[/red] {result.workflow_id}: {err}")
            errors += 1
        for warn in result.warnings:
            err_console.print(f"[yellow]WARNING:[/yellow] {result.workflow_id}: {warn}")
            warnings += 1
        if result.ok and not result.warnings and verbose:
            console.print(f"[green]\u2713[/green] {result.workflow_id}")

    if not quiet:
        console.print()

    # Summary
    if errors > 0:
        console.print(f"[red]Validation failed: {errors} errors, {warnings} warnings[/red]")
        raise typer.Exit(1)
    elif warnings > 0:
        console.print(f"[yellow]Validation passed with {warnings} warnings[/yellow]")
    else:
        console.print("[green]Validation passed[/green]")
