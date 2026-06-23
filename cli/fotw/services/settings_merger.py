"""Non-destructive JSON merging for Claude Code settings.json."""

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


def merge_env(existing_settings: dict, env_vars: dict[str, str]) -> dict:
    """Merge environment variables into settings.json env block."""
    merged = dict(existing_settings)
    merged.setdefault("env", {})
    merged["env"].update(env_vars)
    return merged


def write_settings(settings: dict, path: Path) -> None:
    """Write settings dict as formatted JSON.

    Writes to a temp file then atomically replaces the target, so an
    interrupted write cannot leave settings.json half-written and corrupt.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".__fotw_tmp")
    tmp.write_text(json.dumps(settings, indent=2) + "\n")
    tmp.replace(path)


# ---------------------------------------------------------------------------
# Persona settings (outputStyle + spinnerVerbs)
#
# These keys are a derived cache of .claude/persona.yaml, never authoritative.
# The previous-value record lives in persona.yaml (fotw-owned), so a user's
# own outputStyle choice (e.g. "Explanatory") survives persona on/off cycles.
# ---------------------------------------------------------------------------

PERSONA_STYLE_PREFIX = "Persona: "


def _fotw_style_active(settings: dict) -> bool:
    style = settings.get("outputStyle")
    return isinstance(style, str) and style.startswith(PERSONA_STYLE_PREFIX)


def merge_output_style(existing_settings: dict, style_name: str) -> dict:
    """Set the outputStyle key, preserving all other settings."""
    merged = dict(existing_settings)
    merged["outputStyle"] = style_name
    return merged


def merge_spinner_verbs(existing_settings: dict, verbs: list[str]) -> dict:
    """Set spinnerVerbs to replace-mode persona verbs, preserving other settings."""
    merged = dict(existing_settings)
    merged["spinnerVerbs"] = {"mode": "replace", "verbs": list(verbs)}
    return merged


def capture_previous(settings: dict, record: dict) -> dict:
    """Record the user's pre-persona outputStyle/spinnerVerbs for later restore.

    Records only when the current values are not fotw-written, and never
    overwrites an existing record — so the original user state is preserved
    across persona A -> persona B switches. Absent values are recorded as
    None, meaning "delete the key on restore".
    """
    new_record = dict(record)
    if "previous-output-style" in new_record or "previous-spinner-verbs" in new_record:
        return new_record
    if _fotw_style_active(settings):
        # Already persona-managed with no prior record: nothing safe to record.
        return new_record
    new_record["previous-output-style"] = settings.get("outputStyle")
    new_record["previous-spinner-verbs"] = settings.get("spinnerVerbs")
    return new_record


def remove_persona_keys(settings: dict, record: dict) -> dict:
    """Deactivate persona settings, restoring recorded previous values.

    Restores only while the current outputStyle is still fotw-written; if the
    user manually changed styles after activation, their choice wins and
    nothing is touched.
    """
    if not _fotw_style_active(settings):
        return dict(settings)
    result = dict(settings)
    previous_style = record.get("previous-output-style")
    if previous_style:
        result["outputStyle"] = previous_style
    else:
        result.pop("outputStyle", None)
    previous_verbs = record.get("previous-spinner-verbs")
    if previous_verbs is not None:
        result["spinnerVerbs"] = previous_verbs
    else:
        result.pop("spinnerVerbs", None)
    return result
