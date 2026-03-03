"""Non-destructive JSON deep-merge for Claude Code settings.json hooks."""

import json
from pathlib import Path

from fotw.models.workflow import Hook


def read_settings(path: Path) -> dict:
    """Read existing settings.json or return empty dict."""
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return {}


def build_hooks_config(hooks: list[Hook]) -> dict[str, list[dict]]:
    """Build a hooks config dict from a list of Hook objects.

    Returns structure like:
        {"PreToolUse": [{"matcher": "Bash", "hooks": [...]}, ...], ...}
    """
    config: dict[str, list[dict]] = {}
    for hook in hooks:
        event = hook.event
        config.setdefault(event, [])
        config[event].append(hook.settings_entry)
    return config


def _entry_command(entry: dict) -> str | None:
    """Extract the command string from a hook entry for dedup."""
    hooks_list = entry.get("hooks", [])
    if hooks_list and isinstance(hooks_list, list):
        return hooks_list[0].get("command")
    return None


def merge_hooks(existing_settings: dict, new_hooks: list[Hook]) -> dict:
    """Merge new hook entries into existing settings, deduplicating by command.

    Preserves all other keys (env, statusLine, enabledPlugins, etc.).
    """
    settings = dict(existing_settings)
    new_config = build_hooks_config(new_hooks)

    existing_hooks = settings.get("hooks", {})
    if not isinstance(existing_hooks, dict):
        existing_hooks = {}

    merged_hooks = dict(existing_hooks)

    for event, new_entries in new_config.items():
        existing_entries = merged_hooks.get(event, [])
        if not isinstance(existing_entries, list):
            existing_entries = []

        # Collect existing commands for dedup
        existing_commands = set()
        for entry in existing_entries:
            cmd = _entry_command(entry)
            if cmd:
                existing_commands.add(cmd)

        # Add only new entries that don't already exist
        for new_entry in new_entries:
            cmd = _entry_command(new_entry)
            if cmd and cmd not in existing_commands:
                existing_entries.append(new_entry)
                existing_commands.add(cmd)

        merged_hooks[event] = existing_entries

    settings["hooks"] = merged_hooks
    return settings


def write_settings(settings: dict, path: Path) -> None:
    """Write settings dict as formatted JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(settings, indent=2) + "\n")
