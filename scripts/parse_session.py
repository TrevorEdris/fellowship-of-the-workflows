#!/usr/bin/env python3
"""
parse_session.py — Extract structured data from a SESSION.md file.

Parses:
  - YAML frontmatter (between leading --- delimiters)
  - Decision entries from the ## Decisions section
  - Prompt blocks from ### Prompt N headings

Usage:
    python3 parse_session.py <path-to-SESSION.md>
    python3 parse_session.py <path-to-SESSION.md> --verbose
    python3 parse_session.py <path-to-SESSION.md> --json   (default output; flag kept for clarity)

Output:
    JSON to stdout with keys:
      schema_version  — "v1" if frontmatter has schema: v1, else "unknown"
      source          — file path
      frontmatter     — dict of parsed YAML fields (empty dict if no frontmatter)
      decisions       — list of {date, text} objects
      prompts         — list of {number, heading, body} objects (body only with --verbose)

Exit codes:
    0 — parse succeeded (even for legacy sessions without frontmatter)
    1 — file not found or unreadable
"""

import argparse
import json
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Frontmatter extraction
# ---------------------------------------------------------------------------

_FM_PATTERN = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def _parse_yaml_simple(text: str) -> dict:
    """
    Parse simple YAML key: value pairs using stdlib only.

    Handles:
      - string scalars: key: value
      - quoted strings: key: "value" or key: 'value'
      - lists: key: [a, b, c]
      - booleans: true/false
      - integers

    Does NOT handle nested mappings or multi-line scalars. SESSION.md
    frontmatter is intentionally flat, so this is sufficient.

    Falls back to PyYAML if available.
    """
    try:
        import yaml  # type: ignore
        return yaml.safe_load(text) or {}
    except ImportError:
        pass

    result: dict = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            continue
        key, _, raw_value = line.partition(":")
        key = key.strip()
        raw_value = raw_value.strip()

        # List: [a, b, c]
        if raw_value.startswith("[") and raw_value.endswith("]"):
            inner = raw_value[1:-1]
            items = [v.strip().strip("\"'") for v in inner.split(",") if v.strip()]
            result[key] = items
            continue

        # Quoted string
        if (raw_value.startswith('"') and raw_value.endswith('"')) or (
            raw_value.startswith("'") and raw_value.endswith("'")
        ):
            result[key] = raw_value[1:-1]
            continue

        # Boolean
        if raw_value.lower() == "true":
            result[key] = True
            continue
        if raw_value.lower() == "false":
            result[key] = False
            continue

        # Integer
        try:
            result[key] = int(raw_value)
            continue
        except ValueError:
            pass

        result[key] = raw_value

    return result


def extract_frontmatter(text: str) -> tuple[dict, str]:
    """
    Return (frontmatter_dict, body_text).

    body_text is the file content after the closing --- delimiter.
    If no frontmatter is present, returns ({}, text).
    """
    match = _FM_PATTERN.match(text)
    if not match:
        return {}, text
    fm = _parse_yaml_simple(match.group(1))
    body = text[match.end():]
    return fm, body


# ---------------------------------------------------------------------------
# Decision extraction
# ---------------------------------------------------------------------------

# Matches: - **YYYY-MM-DD** — text  OR  - **YYYY-MM-DD** - text
_DECISION_PATTERN = re.compile(
    r"^\s*-\s*\*\*(\d{4}-\d{2}-\d{2})\*\*\s*[—\-]+\s*(.+)$",
    re.MULTILINE,
)

# Heading that marks the start of the decisions section
_DECISIONS_HEADING = re.compile(r"^#{1,3}\s+Decisions\b", re.MULTILINE | re.IGNORECASE)

# Any heading of level 1 or 2 (used to find end of decisions section)
_NEXT_MAJOR_HEADING = re.compile(r"^#{1,2}\s+\S", re.MULTILINE)


def extract_decisions(body: str) -> list[dict]:
    """
    Find the ## Decisions section and extract dated decision entries.

    Also scans the full body for any decision entries outside the canonical
    section (e.g. legacy sessions using ## Key Decisions).

    Returns list of {date, text} dicts, deduplicated.
    """
    decisions = []
    seen: set[str] = set()

    def _add(date: str, text: str) -> None:
        key = f"{date}|{text}"
        if key not in seen:
            seen.add(key)
            decisions.append({"date": date, "text": text.strip()})

    # Scan the canonical section first (if present), then the full body.
    # Scanning the section first preserves ordering; full-body scan catches legacy layouts.
    section_match = _DECISIONS_HEADING.search(body)
    if section_match:
        section_start = section_match.end()
        # Find where the section ends (next heading of equal or higher level)
        next_heading = _NEXT_MAJOR_HEADING.search(body, section_start)
        section_end = next_heading.start() if next_heading else len(body)
        section_text = body[section_start:section_end]
        for m in _DECISION_PATTERN.finditer(section_text):
            _add(m.group(1), m.group(2))

    # Full-body scan to catch decisions outside canonical section
    for m in _DECISION_PATTERN.finditer(body):
        _add(m.group(1), m.group(2))

    return decisions


# ---------------------------------------------------------------------------
# Prompt block extraction
# ---------------------------------------------------------------------------

# Matches ### Prompt N  or  ### Prompt N (YYYY-MM-DD)
_PROMPT_HEADING = re.compile(
    r"^###\s+Prompt\s+(\d+)(?:\s+\((\d{4}-\d{2}-\d{2})\))?\s*$",
    re.MULTILINE | re.IGNORECASE,
)

# Any heading of level 3 or higher marks end of a prompt block
_ANY_HEADING = re.compile(r"^#{1,6}\s+\S", re.MULTILINE)


def extract_prompts(body: str, include_body: bool = False) -> list[dict]:
    """
    Extract prompt blocks from ### Prompt N headings.

    Returns list of {number, date, heading, body} dicts.
    body is included only if include_body=True (--verbose mode).
    """
    prompts = []
    matches = list(_PROMPT_HEADING.finditer(body))

    for idx, match in enumerate(matches):
        number = int(match.group(1))
        date = match.group(2)  # may be None
        block_start = match.end()

        # Find end of block: next heading at any level, or end of body
        next_headings = [
            m.start()
            for m in _ANY_HEADING.finditer(body, block_start)
        ]
        block_end = next_headings[0] if next_headings else len(body)
        block_text = body[block_start:block_end].strip()

        entry: dict = {
            "number": number,
            "heading": match.group(0).strip(),
        }
        if date:
            entry["date"] = date
        if include_body:
            entry["body"] = block_text
        else:
            # Include a short preview (first 120 chars) without the full body
            preview = block_text[:120].replace("\n", " ").strip()
            if len(block_text) > 120:
                preview += "…"
            entry["preview"] = preview

        prompts.append(entry)

    return prompts


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def parse_session(path: Path, verbose: bool = False) -> dict:
    """Parse a SESSION.md and return structured data."""
    text = path.read_text(encoding="utf-8")
    frontmatter, body = extract_frontmatter(text)
    schema_version = frontmatter.get("schema", "unknown")
    if schema_version != "unknown":
        schema_version = str(schema_version)

    decisions = extract_decisions(body)
    prompts = extract_prompts(body, include_body=verbose)

    return {
        "schema_version": schema_version,
        "source": str(path),
        "frontmatter": frontmatter,
        "decisions": decisions,
        "prompts": prompts,
        "counts": {
            "decisions": len(decisions),
            "prompts": len(prompts),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Extract structured data from a SESSION.md file."
    )
    parser.add_argument("path", help="Path to SESSION.md file")
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Include full prompt body text in output",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON (default; flag kept for clarity)",
    )
    args = parser.parse_args()

    source = Path(args.path)
    if not source.exists():
        print(f"ERROR: file not found: {source}", file=sys.stderr)
        return 1
    if not source.is_file():
        print(f"ERROR: not a file: {source}", file=sys.stderr)
        return 1

    result = parse_session(source, verbose=args.verbose)
    print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
