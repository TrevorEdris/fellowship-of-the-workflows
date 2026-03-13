"""Typer application and command registration."""

import typer

from fotw.commands.install import install_cmd
from fotw.commands.list import list_cmd
from fotw.commands.new import new_cmd
from fotw.commands.setup import setup_cmd
from fotw.commands.update import update_cmd
from fotw.commands.validate import validate_cmd

app = typer.Typer(
    name="fotw",
    help="Fellowship of the Workflows CLI",
    no_args_is_help=True,
)

app.command("install")(install_cmd)
app.command("list")(list_cmd)
app.command("new")(new_cmd)
app.command("setup")(setup_cmd)
app.command("update")(update_cmd)
app.command("validate")(validate_cmd)
