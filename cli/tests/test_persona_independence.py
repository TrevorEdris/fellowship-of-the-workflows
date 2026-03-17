"""Tests ensuring workflow files contain no persona-specific elements.

Workflow files (skills, agents, rules) must be persona-agnostic.
The persona system handles voice/style at runtime via persona.yaml.
"""

import re

import pytest

from fotw.services.catalog import COMMUNITY_AGENTS_DIR, COMMUNITY_RULES_DIR, WORKFLOWS_DIR

# Persona character names — specific enough to avoid false positives.
# Intentionally excludes generic words like "enterprise", "neighborhood"
# that appear legitimately in tech contexts.
PERSONA_TERMS = {
    # Lord of the Rings
    "gandalf", "treebeard", "aragorn", "legolas", "gimli", "frodo",
    "samwise", "bilbo", "sauron", "saruman", "gollum", "maiar",
    "mithrandir", "istari",
    # Star Wars
    "yoda", "padawan", "lightsaber",
    # Star Trek
    "picard", "spock", "starfleet", "vulcan",
    # Big Lebowski
    "lebowski",
    # Bob Ross
    "bob ross",
    # Mr Rogers
    "mister rogers",
    # Attenborough
    "attenborough",
    # Ron Swanson
    "ron swanson", "swanson",
    # Monty Python
    "monty python", "holy grail",
    # Chewbacca
    "chewbacca", "chewie", "wookiee",
    # Princess Bride
    "princess bride", "inconceivable",
}

# Project conventions that look persona-like but are intentional.
# This set should be empty or near-empty. If you need to add entries here,
# consider whether the persona language belongs in the workflow file at all.
ALLOWED_PATTERNS: set[str] = set()

# Skills whose purpose is managing personas — they legitimately reference persona names.
PERSONA_MANAGEMENT_SKILLS = {"switch-persona", "create-persona"}

# Build a single regex for efficiency
_TERM_PATTERN = re.compile(
    "|".join(re.escape(term) for term in sorted(PERSONA_TERMS, key=len, reverse=True)),
    re.IGNORECASE,
)


def _scan_file_for_persona_terms(filepath):
    """Return list of (line_number, line, matched_term) tuples."""
    violations = []

    # Quick skip: if no persona term appears at all, skip line-by-line scan
    if not _TERM_PATTERN.search(filepath.read_text()):
        return violations

    for line_num, line in enumerate(filepath.read_text().splitlines(), start=1):
        for match in _TERM_PATTERN.finditer(line):
            matched = match.group().lower()
            # Check if this match is part of an allowed pattern
            line_lower = line.lower()
            if any(allowed in line_lower for allowed in ALLOWED_PATTERNS):
                continue
            violations.append((line_num, line.strip(), matched))

    return violations


def _format_violations(filepath, violations):
    """Format violation report for assertion message."""
    lines = [f"\n  {filepath}:"]
    for line_num, line, term in violations:
        lines.append(f"    L{line_num}: matched '{term}' in: {line[:100]}")
    return "\n".join(lines)


# --- Rules ---


def test_no_persona_terms_in_rules():
    """Rules must not contain persona-specific names or terms."""
    all_violations = []
    for rules_dir in [WORKFLOWS_DIR / "rules", COMMUNITY_RULES_DIR]:
        if not rules_dir.is_dir():
            continue
        for path in sorted(rules_dir.iterdir()):
            if path.suffix not in (".mdc", ".md"):
                continue
            violations = _scan_file_for_persona_terms(path)
            if violations:
                all_violations.append(_format_violations(path, violations))

    assert not all_violations, f"Persona terms found in rules:{''.join(all_violations)}"


# --- Skills ---


def test_no_persona_terms_in_skills():
    """Skill files must not contain persona-specific names or terms.

    Excludes persona-management skills (switch-persona, create-persona)
    which legitimately reference persona names.
    """
    skills_dir = WORKFLOWS_DIR / "skills"
    if not skills_dir.is_dir():
        pytest.skip("No skills directory")

    all_violations = []
    for skill_dir in sorted(skills_dir.iterdir()):
        if not skill_dir.is_dir():
            continue
        if skill_dir.name in PERSONA_MANAGEMENT_SKILLS:
            continue
        for path in sorted(skill_dir.rglob("*.md")):
            violations = _scan_file_for_persona_terms(path)
            if violations:
                all_violations.append(_format_violations(path, violations))

    assert not all_violations, f"Persona terms found in skills:{''.join(all_violations)}"


# --- Agents ---


def test_no_persona_terms_in_agents():
    """Agent definitions must not contain persona-specific names or terms."""
    all_violations = []
    for agents_dir in [WORKFLOWS_DIR / "agents", COMMUNITY_AGENTS_DIR]:
        if not agents_dir.is_dir():
            continue
        for path in sorted(agents_dir.iterdir()):
            if path.suffix != ".md":
                continue
            violations = _scan_file_for_persona_terms(path)
            if violations:
                all_violations.append(_format_violations(path, violations))

    assert not all_violations, f"Persona terms found in agents:{''.join(all_violations)}"
