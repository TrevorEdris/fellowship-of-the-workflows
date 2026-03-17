"""Tests for cross-reference integrity, catalog consistency, and file hygiene.

Covers:
- Agent catalog consistency (every agent file ↔ catalog entry)
- Skill-agent cross-references (agent: field points to real agent)
- Starter tier rules exist
- Hooks.json integrity (referenced scripts exist)
- File hygiene (newlines, empty files)
"""

import json
import re

import frontmatter
import pytest

from fotw.services.catalog import COMMUNITY_AGENTS_DIR, COMMUNITY_RULES_DIR, WORKFLOWS_DIR, STARTERS_DIR
from fotw.services.installer import TIER_RULES


def _parse(path):
    post = frontmatter.load(str(path))
    return dict(post.metadata)


# --- Agent catalog consistency ---


CATALOG_PATH = WORKFLOWS_DIR / "skills" / "orchestrate" / "references" / "agent-catalog.md"


def _catalog_agent_names():
    """Extract agent names from the catalog routing table."""
    if not CATALOG_PATH.is_file():
        return set()
    text = CATALOG_PATH.read_text()
    # Match backtick-wrapped agent names in the first column of the routing table
    # Pattern: | `agent-name` |
    return set(re.findall(r"\|\s*`([^`]+)`\s*\|", text))


def _agent_file_names():
    """Return set of agent names from agents/*.md and community/agents/*.md."""
    names = set()
    for agents_dir in [WORKFLOWS_DIR / "agents", COMMUNITY_AGENTS_DIR]:
        if agents_dir.is_dir():
            names.update(p.stem for p in agents_dir.glob("*.md") if p.name != ".gitkeep")
    return names


def test_all_agents_in_catalog():
    """Every agent file must have a corresponding entry in the agent catalog."""
    if not CATALOG_PATH.is_file():
        pytest.skip("Agent catalog not found")

    file_agents = _agent_file_names()
    catalog_agents = _catalog_agent_names()
    missing = file_agents - catalog_agents

    assert not missing, (
        f"Agents missing from catalog ({CATALOG_PATH.name}):\n"
        + "\n".join(f"  - {a}" for a in sorted(missing))
    )


def test_no_stale_catalog_entries():
    """Every agent in the catalog must have a corresponding agent file."""
    if not CATALOG_PATH.is_file():
        pytest.skip("Agent catalog not found")

    file_agents = _agent_file_names()
    catalog_agents = _catalog_agent_names()
    stale = catalog_agents - file_agents

    assert not stale, (
        f"Stale catalog entries (no matching agent file):\n"
        + "\n".join(f"  - {a}" for a in sorted(stale))
    )


# --- Skill-agent cross-references ---


def test_skill_agent_references_exist():
    """If a skill's frontmatter has 'agent: foo', agents/foo.md must exist."""
    skills_dir = WORKFLOWS_DIR / "skills"
    if not skills_dir.is_dir():
        pytest.skip("No skills directory")

    broken = []
    for skill_dir in sorted(skills_dir.iterdir()):
        if not skill_dir.is_dir():
            continue
        skill_file = skill_dir / "SKILL.md"
        if not skill_file.is_file():
            continue
        meta = _parse(skill_file)
        agent_ref = meta.get("agent")
        if agent_ref:
            core_path = WORKFLOWS_DIR / "agents" / f"{agent_ref}.md"
            community_path = COMMUNITY_AGENTS_DIR / f"{agent_ref}.md"
            if not core_path.is_file() and not community_path.is_file():
                broken.append(f"{skill_dir.name}: agent='{agent_ref}' -> file not found")

    assert not broken, f"Broken skill-agent references:\n" + "\n".join(broken)


# --- Starter validation ---


def test_starter_tier_rules_exist():
    """Every rule referenced in TIER_RULES must exist in rules/."""
    rules_dir = WORKFLOWS_DIR / "rules"
    missing = []

    for tier, rules in TIER_RULES.items():
        for rule_name in rules:
            mdc = rules_dir / f"{rule_name}.mdc"
            md = rules_dir / f"{rule_name}.md"
            if not mdc.is_file() and not md.is_file():
                missing.append(f"{tier} tier: '{rule_name}' not found")

    assert not missing, f"Missing tier rules:\n" + "\n".join(missing)


# --- Hooks.json integrity ---


def test_hooks_json_references_exist():
    """Every script referenced in hooks.json must exist on disk."""
    hooks_json = WORKFLOWS_DIR / "hooks" / "hooks.json"
    if not hooks_json.is_file():
        pytest.skip("No hooks/hooks.json")

    data = json.loads(hooks_json.read_text())
    hooks_dir = WORKFLOWS_DIR / "hooks"
    missing = []

    for _event, entries in data.get("hooks", {}).items():
        for entry in entries:
            for hook in entry.get("hooks", []):
                cmd = hook.get("command", "")
                # Extract filename from ${CLAUDE_PLUGIN_ROOT}/hooks/<name>.js
                if "/hooks/" in cmd:
                    filename = cmd.split("/hooks/")[-1]
                    if not (hooks_dir / filename).is_file():
                        missing.append(f"{cmd} -> {filename} not found")

    assert not missing, (
        f"hooks.json references missing scripts:\n"
        + "\n".join(f"  - {m}" for m in missing)
    )


def test_hooks_json_valid_structure():
    """hooks.json must be valid JSON with expected structure."""
    hooks_json = WORKFLOWS_DIR / "hooks" / "hooks.json"
    if not hooks_json.is_file():
        pytest.skip("No hooks/hooks.json")

    data = json.loads(hooks_json.read_text())
    assert "hooks" in data, "hooks.json must have a top-level 'hooks' key"

    from fotw.services.catalog import KNOWN_HOOK_EVENTS
    for event in data["hooks"]:
        assert event in KNOWN_HOOK_EVENTS, f"Unknown event in hooks.json: {event}"


def test_starter_files_exist():
    """minimal.md, standard.md, full.md must all exist in starters/."""
    for tier in ("minimal", "standard", "full"):
        path = STARTERS_DIR / f"{tier}.md"
        assert path.is_file(), f"Missing starter: {path}"


# --- File hygiene ---


def test_all_workflow_files_end_with_newline():
    """All workflow markdown files should end with a newline (POSIX)."""
    violations = []

    # Rules (core + community)
    for rules_dir in [WORKFLOWS_DIR / "rules", COMMUNITY_RULES_DIR]:
        if rules_dir.is_dir():
            for path in sorted(rules_dir.iterdir()):
                if path.suffix not in (".mdc", ".md") or path.name == ".gitkeep":
                    continue
                content = path.read_text()
                if content and not content.endswith("\n"):
                    violations.append(str(path))

    # Skills
    skills_dir = WORKFLOWS_DIR / "skills"
    if skills_dir.is_dir():
        for skill_dir in sorted(skills_dir.iterdir()):
            if not skill_dir.is_dir():
                continue
            for path in skill_dir.rglob("*.md"):
                content = path.read_text()
                if content and not content.endswith("\n"):
                    violations.append(str(path))

    # Agents (core + community)
    for agents_dir in [WORKFLOWS_DIR / "agents", COMMUNITY_AGENTS_DIR]:
        if agents_dir.is_dir():
            for path in sorted(agents_dir.iterdir()):
                if path.suffix != ".md" or path.name == ".gitkeep":
                    continue
                content = path.read_text()
                if content and not content.endswith("\n"):
                    violations.append(str(path))

    assert not violations, (
        f"Files missing trailing newline:\n" + "\n".join(f"  - {v}" for v in violations)
    )


def test_no_empty_workflow_files():
    """No workflow file should be zero bytes."""
    empty = []

    for rules_dir in [WORKFLOWS_DIR / "rules", COMMUNITY_RULES_DIR]:
        if rules_dir.is_dir():
            for path in sorted(rules_dir.glob("*")):
                if path.suffix in (".mdc", ".md") and path.stat().st_size == 0:
                    empty.append(str(path))

    for skill_dir in sorted((WORKFLOWS_DIR / "skills").iterdir()):
        if skill_dir.is_dir():
            skill_file = skill_dir / "SKILL.md"
            if skill_file.is_file() and skill_file.stat().st_size == 0:
                empty.append(str(skill_file))

    for agents_dir in [WORKFLOWS_DIR / "agents", COMMUNITY_AGENTS_DIR]:
        if agents_dir.is_dir():
            for path in sorted(agents_dir.glob("*.md")):
                if path.stat().st_size == 0:
                    empty.append(str(path))

    assert not empty, f"Empty workflow files:\n" + "\n".join(f"  - {e}" for e in empty)
