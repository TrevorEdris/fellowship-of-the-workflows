"""Read/write helpers for the fotw-owned persona.yaml config.

persona.yaml is the runtime source of truth for persona identity and
intensity across all tool targets. It also carries the previous-value record
(previous-output-style, previous-spinner-verbs) used to restore a user's own
Claude Code settings when a persona is switched off.
"""

from pathlib import Path

import yaml

RECORD_KEYS = ("previous-output-style", "previous-spinner-verbs")


def read_persona_config(path: Path) -> dict:
    """Read persona.yaml, returning {} when missing or unparseable."""
    if not path.is_file():
        return {}
    try:
        data = yaml.safe_load(path.read_text())
    except yaml.YAMLError:
        return {}
    return data if isinstance(data, dict) else {}


def write_persona_config(path: Path, config: dict) -> None:
    """Write persona.yaml preserving a stable, human-friendly key order."""
    ordered = {}
    for key in ("persona", "intensity", *RECORD_KEYS):
        if key in config:
            ordered[key] = config[key]
    for key, value in config.items():
        if key not in ordered:
            ordered[key] = value
    path.write_text(yaml.safe_dump(ordered, sort_keys=False, allow_unicode=True))
