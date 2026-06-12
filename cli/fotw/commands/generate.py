"""fotw generate — regenerate derived artifacts committed to the repo."""

import typer

from fotw.services.output_styles import OUTPUT_STYLES_DIR, OutputStyleError, generate_all
from fotw.ui.console import console, err_console


def generate_cmd(
    artifact: str = typer.Argument(
        ..., help="Artifact class to generate. Supported: output-styles"
    ),
) -> None:
    """Regenerate derived artifacts (e.g. persona output styles) from their sources."""
    if artifact != "output-styles":
        err_console.print(f"[red]Unknown artifact: {artifact}[/red]")
        err_console.print("Supported: output-styles")
        raise typer.Exit(1)

    try:
        written = generate_all(OUTPUT_STYLES_DIR)
    except OutputStyleError as exc:
        err_console.print(f"[red]Generation failed: {exc}[/red]")
        raise typer.Exit(1) from exc

    for path in written:
        console.print(f"[green]✓[/green] {path.relative_to(OUTPUT_STYLES_DIR.parent)}")
    console.print(f"Generated {len(written)} output styles in {OUTPUT_STYLES_DIR}/")
