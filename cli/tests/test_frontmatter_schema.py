"""Tests enforcing strict frontmatter schemas for all workflow types.

Every frontmatter key must belong to the allowed set for its type.
Required fields must be present. Values must be valid.
"""

import frontmatter
import pytest

from fotw.models.workflow import VALID_TAGS
from fotw.services.catalog import WORKFLOWS_DIR, _EXTRA_AGENT_DIRS, _EXTRA_RULE_DIRS

# --- Allowed frontmatter keys per workflow type ---

RULE_ALLOWED_KEYS = {"description", "globs", "alwaysApply"}

SKILL_ALLOWED_KEYS = {
    "name",
    "description",
    "context",
    "agent",
    "allowed-tools",
    "model",
    "argument-hint",
    "disable-model-invocation",
    "user-invocable",
    "tags",
}

AGENT_ALLOWED_KEYS = {"name", "description", "tools", "model", "color"}

VALID_MODEL_VALUES = {"opus", "sonnet", "haiku", "default"}


def _parse(path):
    """Parse frontmatter from a file, return metadata dict."""
    post = frontmatter.load(str(path))
    return dict(post.metadata)


# --- Rules ---


def _iter_rule_files():
    """Yield all rule files from core and language/platform/vendor dirs."""
    for rules_dir, _ in [(WORKFLOWS_DIR / "rules", "core")] + _EXTRA_RULE_DIRS:
        if rules_dir.is_dir():
            for path in sorted(rules_dir.iterdir()):
                if path.suffix in (".mdc", ".md") and path.name != ".gitkeep":
                    yield path


def test_rules_no_extra_frontmatter_keys():
    """Every rule frontmatter key must be in the allowed set."""
    violations = []
    for path in _iter_rule_files():
        meta = _parse(path)
        extra = set(meta.keys()) - RULE_ALLOWED_KEYS
        if extra:
            violations.append(f"{path.name}: unexpected keys {extra}")

    assert not violations, f"Rules with extra frontmatter keys:\n" + "\n".join(violations)


def test_rules_required_frontmatter():
    """Every rule must have a description."""
    missing = []
    for path in _iter_rule_files():
        meta = _parse(path)
        if not meta.get("description"):
            missing.append(path.name)

    assert not missing, f"Rules missing 'description': {missing}"


# --- Skills ---


def test_skills_no_extra_frontmatter_keys():
    """Every skill frontmatter key must be in the allowed set."""
    skills_dir = WORKFLOWS_DIR / "skills"
    if not skills_dir.is_dir():
        pytest.skip("No skills directory")

    violations = []
    for skill_dir in sorted(skills_dir.iterdir()):
        if not skill_dir.is_dir():
            continue
        skill_file = skill_dir / "SKILL.md"
        if not skill_file.is_file():
            continue
        meta = _parse(skill_file)
        extra = set(meta.keys()) - SKILL_ALLOWED_KEYS
        if extra:
            violations.append(f"{skill_dir.name}: unexpected keys {extra}")

    assert not violations, f"Skills with extra frontmatter keys:\n" + "\n".join(violations)


def test_skills_required_frontmatter():
    """Every skill must have name and description."""
    skills_dir = WORKFLOWS_DIR / "skills"
    if not skills_dir.is_dir():
        pytest.skip("No skills directory")

    violations = []
    for skill_dir in sorted(skills_dir.iterdir()):
        if not skill_dir.is_dir():
            continue
        skill_file = skill_dir / "SKILL.md"
        if not skill_file.is_file():
            continue
        meta = _parse(skill_file)
        missing = []
        if not meta.get("name"):
            missing.append("name")
        if not meta.get("description"):
            missing.append("description")
        if missing:
            violations.append(f"{skill_dir.name}: missing {missing}")

    assert not violations, f"Skills with missing required fields:\n" + "\n".join(violations)


def test_skill_tags_valid_values():
    """Skill 'tags' values, if present, must be from the controlled vocabulary."""
    skills_dir = WORKFLOWS_DIR / "skills"
    if not skills_dir.is_dir():
        pytest.skip("No skills directory")

    invalid = []
    for skill_dir in sorted(skills_dir.iterdir()):
        if not skill_dir.is_dir():
            continue
        skill_file = skill_dir / "SKILL.md"
        if not skill_file.is_file():
            continue
        meta = _parse(skill_file)
        tags = meta.get("tags", [])
        if not tags:
            continue
        bad = [t for t in tags if t not in VALID_TAGS]
        if bad:
            invalid.append(f"{skill_dir.name}: invalid tags {bad}")

    assert not invalid, f"Skills with invalid tag values:\n" + "\n".join(invalid)


def test_skill_tags_is_list():
    """Skill 'tags' field, if present, must be a list."""
    skills_dir = WORKFLOWS_DIR / "skills"
    if not skills_dir.is_dir():
        pytest.skip("No skills directory")

    violations = []
    for skill_dir in sorted(skills_dir.iterdir()):
        if not skill_dir.is_dir():
            continue
        skill_file = skill_dir / "SKILL.md"
        if not skill_file.is_file():
            continue
        meta = _parse(skill_file)
        tags = meta.get("tags")
        if tags is not None and not isinstance(tags, list):
            violations.append(f"{skill_dir.name}: tags is {type(tags).__name__}, expected list")

    assert not violations, f"Skills with non-list tags:\n" + "\n".join(violations)


def test_skill_name_matches_directory():
    """Skill frontmatter 'name' must match the directory name."""
    skills_dir = WORKFLOWS_DIR / "skills"
    if not skills_dir.is_dir():
        pytest.skip("No skills directory")

    mismatches = []
    for skill_dir in sorted(skills_dir.iterdir()):
        if not skill_dir.is_dir():
            continue
        skill_file = skill_dir / "SKILL.md"
        if not skill_file.is_file():
            continue
        meta = _parse(skill_file)
        name = meta.get("name", "")
        if name and name != skill_dir.name:
            mismatches.append(f"{skill_dir.name}: frontmatter name='{name}'")

    assert not mismatches, f"Skill name/directory mismatches:\n" + "\n".join(mismatches)


# --- Agents ---


def _iter_agent_files():
    """Yield all agent files from core and platform/vendor dirs."""
    for agents_dir, _ in [(WORKFLOWS_DIR / "agents", "core")] + _EXTRA_AGENT_DIRS:
        if agents_dir.is_dir():
            for path in sorted(agents_dir.iterdir()):
                if path.suffix == ".md" and path.name != ".gitkeep":
                    yield path


def test_agents_no_extra_frontmatter_keys():
    """Every agent frontmatter key must be in the allowed set."""
    violations = []
    for path in _iter_agent_files():
        meta = _parse(path)
        extra = set(meta.keys()) - AGENT_ALLOWED_KEYS
        if extra:
            violations.append(f"{path.name}: unexpected keys {extra}")

    assert not violations, f"Agents with extra frontmatter keys:\n" + "\n".join(violations)


def test_agents_required_frontmatter():
    """Every agent must have name and description."""
    violations = []
    for path in _iter_agent_files():
        meta = _parse(path)
        missing = []
        if not meta.get("name"):
            missing.append("name")
        if not meta.get("description"):
            missing.append("description")
        if missing:
            violations.append(f"{path.stem}: missing {missing}")

    assert not violations, f"Agents with missing required fields:\n" + "\n".join(violations)


# --- Model field validation (shared across skills and agents) ---


def test_skill_model_valid_values():
    """Skill 'model' field, if present, must be opus/sonnet/haiku."""
    skills_dir = WORKFLOWS_DIR / "skills"
    if not skills_dir.is_dir():
        pytest.skip("No skills directory")

    invalid = []
    for skill_dir in sorted(skills_dir.iterdir()):
        if not skill_dir.is_dir():
            continue
        skill_file = skill_dir / "SKILL.md"
        if not skill_file.is_file():
            continue
        meta = _parse(skill_file)
        model = meta.get("model")
        if model and model not in VALID_MODEL_VALUES:
            invalid.append(f"{skill_dir.name}: model='{model}'")

    assert not invalid, f"Skills with invalid model values:\n" + "\n".join(invalid)


def test_agent_model_valid_values():
    """Agent 'model' field, if present, must be opus/sonnet/haiku."""
    invalid = []
    for path in _iter_agent_files():
        meta = _parse(path)
        model = meta.get("model")
        if model and model not in VALID_MODEL_VALUES:
            invalid.append(f"{path.stem}: model='{model}'")

    assert not invalid, f"Agents with invalid model values:\n" + "\n".join(invalid)
