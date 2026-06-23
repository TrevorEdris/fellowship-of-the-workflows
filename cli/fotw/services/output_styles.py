"""Deterministic generator: personas/*.md -> Claude Code output styles.

Generation is pure positional extraction from the shared persona template
structure — no model calls — so CI can verify committed styles byte-for-byte
(see test_committed_styles_are_fresh). Edit a persona, then regenerate with
`fotw generate output-styles`.

Generated styles are self-sufficient: plugin-only installs have no personas/
or rules/ on disk, so the style body never references the source file. The
body defers to .claude/persona.yaml for both identity and intensity, keeping
persona.yaml the single runtime source of truth.
"""

from pathlib import Path

from fotw.services.catalog import PERSONAS_DIR, REPO_ROOT

OUTPUT_STYLES_DIR = REPO_ROOT / "output-styles"

# Extraction limits — fixed so generation stays deterministic
SPEECH_PATTERN_COUNT = 3
SIGNATURE_PHRASE_COUNT = 4

INTENSITY_TABLE = """\
| Intensity | Behavior |
|-----------|----------|
| `off` | Standard professional responses. No persona flavor. |
| `minimal` | Flavor at key moments only: session start/end, warnings, phase transitions. |
| `noticeable` | Light flavor in most responses. Always use the persona's phase names and severity levels. |
| `excessive` | Full character immersion. Every response heavily flavored. |"""

BOUNDARIES = """\
- Code, comments, commit messages, PR descriptions, and all file contents are always written in normal professional voice. The persona lives only in conversation.
- Security warnings, destructive-action confirmations, and multi-step instructions drop the persona entirely for clarity.
- The persona is flavor, never obstruction. Technical substance always comes first."""


class OutputStyleError(Exception):
    """Raised when a persona file cannot be converted to an output style."""


def _read_lines(path: Path) -> list[str]:
    try:
        return path.read_text().splitlines()
    except OSError as exc:
        raise OutputStyleError(f"{path.name}: cannot read persona file: {exc}") from exc


def _persona_name(lines: list[str], path: Path) -> str:
    if not lines or not lines[0].startswith("# Persona: "):
        raise OutputStyleError(f"{path.name}: first line must be '# Persona: <Name>'")
    return lines[0][len("# Persona: "):].strip()


def _tagline(lines: list[str], path: Path) -> str:
    if len(lines) < 3 or not lines[2].startswith("> "):
        raise OutputStyleError(f"{path.name}: line 3 must be the blockquote tagline")
    return lines[2][2:].strip()


def _section(lines: list[str], heading: str, path: Path) -> list[str]:
    """Return the lines of a section (any level) until the next same-or-higher heading."""
    level = heading.split(" ")[0]  # '##' or '###'
    try:
        start = lines.index(heading)
    except ValueError:
        raise OutputStyleError(f"{path.name}: missing required section '{heading}'") from None
    body = []
    for line in lines[start + 1:]:
        if line.startswith("#") and len(line.split(" ")[0]) <= len(level):
            break
        body.append(line)
    return body


def _bullets(section_lines: list[str]) -> list[str]:
    return [line[2:].strip() for line in section_lines if line.startswith("- ")]


def _table_rows(section_lines: list[str]) -> list[list[str]]:
    """Parse markdown table rows (skipping header and separator)."""
    rows = []
    for line in section_lines:
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if all(set(c) <= {"-", " ", ":"} for c in cells):
            continue  # separator row
        rows.append(cells)
    return rows[1:] if rows else []  # drop header row


def _required_bullets(lines: list[str], heading: str, path: Path) -> list[str]:
    items = _bullets(_section(lines, heading, path))
    if not items:
        raise OutputStyleError(f"{path.name}: section '{heading}' has no bullet entries")
    return items


def style_name(path: Path) -> str:
    """Display name of the generated style, e.g. 'Persona: Gandalf'."""
    lines = _read_lines(path)
    return f"Persona: {_persona_name(lines, path)}"


def style_filename(path: Path) -> str:
    """File name of the generated style, e.g. 'persona-gandalf.md'."""
    return f"persona-{path.stem}.md"


SPINNER_VERB_MIN = 10
SPINNER_VERB_MAX = 20
SPINNER_VERB_MAXLEN = 25


def parse_spinner_verbs(path: Path) -> list[str]:
    """Extract and validate the '## Spinner Verbs' entries from a persona file.

    Enforces the same contract the tests assert (10-20 entries, each <= 25
    chars) at the parser, so a malformed persona fails at install time rather
    than only in CI.
    """
    lines = _read_lines(path)
    verbs = _required_bullets(lines, "## Spinner Verbs", path)
    if not SPINNER_VERB_MIN <= len(verbs) <= SPINNER_VERB_MAX:
        raise OutputStyleError(
            f"{path.name}: expected {SPINNER_VERB_MIN}-{SPINNER_VERB_MAX} spinner verbs, found {len(verbs)}"
        )
    for verb in verbs:
        if len(verb) > SPINNER_VERB_MAXLEN:
            raise OutputStyleError(
                f"{path.name}: spinner verb over {SPINNER_VERB_MAXLEN} chars: '{verb}' ({len(verb)})"
            )
    return verbs


def generate_style(path: Path) -> str:
    """Generate the complete output-style markdown for one persona file."""
    lines = _read_lines(path)
    name = _persona_name(lines, path)
    slug = path.stem
    tagline = _tagline(lines, path)

    speech = _required_bullets(lines, "### Speech Patterns", path)[:SPEECH_PATTERN_COUNT]
    phrases = _required_bullets(lines, "### Signature Phrases", path)[:SIGNATURE_PHRASE_COUNT]
    never = _required_bullets(lines, "### Never Says", path)

    phase_rows = _table_rows(_section(lines, "### Phase Names", path))
    severity_rows = _table_rows(_section(lines, "### Severity Levels", path))
    theme_rows = _table_rows(_section(lines, "## Thematic Mappings", path))
    if not phase_rows or not severity_rows or not theme_rows:
        raise OutputStyleError(
            f"{path.name}: Phase Names, Severity Levels, and Thematic Mappings tables are required"
        )

    quotes = []
    for quote_heading in ("### Greetings", "### Warnings", "### General Wisdom"):
        quote = _required_bullets(lines, quote_heading, path)[0]
        quotes.append(quote.strip('"'))

    phases = "; ".join(f"{row[0]} → {row[1]}" for row in phase_rows)
    severities = "; ".join(
        f"{row[0]} → {row[1]}" for row in severity_rows if len(row) >= 2
    )
    themes = "; ".join(f"{row[0]} → {row[1]}" for row in theme_rows if len(row) >= 2)

    def block(items: list[str]) -> str:
        return "\n".join(f"- {item}" for item in items)

    anchors = "\n".join(f'- "{quote}"' for quote in quotes)

    return f"""---
name: "Persona: {name}"
description: "{tagline}"
keep-coding-instructions: true
---

Adopt the voice of {name} while doing your normal engineering work.

## Active-config check

If `.claude/persona.yaml` exists, read it first. If its `persona` is not `{slug}`, or its `intensity` is `off`, ignore this style's voice entirely and follow `persona.yaml` instead. If the file does not exist, use intensity `noticeable`.

{INTENSITY_TABLE}

## Voice

{tagline}

Speech patterns:
{block(speech)}

Signature phrases:
{block(phrases)}

Never:
{block(never)}

## Structure

Phase names: {phases}.

Severity levels: {severities}.

Thematic mappings: {themes}.

## Anchors

These are examples of the voice, not a script — generate fresh material in this register:
{anchors}

## Boundaries

{BOUNDARIES}
"""


def generate_all(target_dir: Path) -> list[Path]:
    """Generate styles for every persona into target_dir. Returns written paths."""
    target_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for path in sorted(PERSONAS_DIR.glob("*.md")):
        if path.name == "_template.md":
            continue
        out = target_dir / style_filename(path)
        out.write_text(generate_style(path))
        written.append(out)
    return written
