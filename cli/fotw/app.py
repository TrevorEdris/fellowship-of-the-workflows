"""Typer application and command registration."""

import typer

from fotw.commands.list import list_cmd
from fotw.commands.validate import validate_cmd

app = typer.Typer(
    name="fotw",
    help="Fellowship of the Workflows CLI",
    no_args_is_help=True,
)

app.command("list")(list_cmd)
app.command("validate")(validate_cmd)
