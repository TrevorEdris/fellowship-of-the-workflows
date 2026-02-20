"""Scan and parse the workflow catalog from disk."""

from pathlib import Path

import frontmatter

from fotw.models.workflow import (
    Persona,
    Starter,
    ValidationResult,
    Workflow,
    WorkflowType,
)


def _repo_root() -> Path:
    """Find the repository root (parent of cli/)."""
    here = Path(__file__).resolve()
    # Walk up until we find bin/ directory (repo root marker)
    for parent in here.parents:
        if (parent / "bin").is_dir() and (parent / "workflows").is_dir():
            return parent
    raise RuntimeError("Cannot locate repository root")


REPO_ROOT = _repo_root()
WORKFLOWS_DIR = REPO_ROOT / "workflows"
STARTERS_DIR = REPO_ROOT / "starters"


def _parse_frontmatter(path: Path) -> dict:
    """Parse YAML frontmatter from a markdown file."""
    try:
        post = frontmatter.load(str(path))
        return dict(post.metadata)
    except Exception:
        return {}


def scan_rules() -> list[Workflow]:
    """Scan workflows/rules/ for rule files."""
    rules_dir = WORKFLOWS_DIR / "rules"
    if not rules_dir.is_dir():
        return []

    results = []
    for path in sorted(rules_dir.iterdir()):
        if path.name == ".gitkeep":
            continue
        if path.suffix not in (".mdc", ".md"):
            continue
        meta = _parse_frontmatter(path)
        results.append(
            Workflow(
                wtype=WorkflowType.RULE,
                name=path.stem,
                description=meta.get("description", ""),
                path=path,
            )
        )
    return results


def scan_skills() -> list[Workflow]:
    """Scan workflows/skills/ for skill directories."""
    skills_dir = WORKFLOWS_DIR / "skills"
    if not skills_dir.is_dir():
        return []

    results = []
    for skill_dir in sorted(skills_dir.iterdir()):
        if not skill_dir.is_dir():
            continue
        skill_file = skill_dir / "SKILL.md"
        if not skill_file.is_file():
            continue
        meta = _parse_frontmatter(skill_file)
        results.append(
            Workflow(
                wtype=WorkflowType.SKILL,
                name=skill_dir.name,
                description=meta.get("description", ""),
                path=skill_dir,
            )
        )
    return results


def scan_agents() -> list[Workflow]:
    """Scan workflows/agents/ for agent files."""
    agents_dir = WORKFLOWS_DIR / "agents"
    if not agents_dir.is_dir():
        return []

    results = []
    for path in sorted(agents_dir.iterdir()):
        if path.name == ".gitkeep":
            continue
        if path.suffix != ".md":
            continue
        meta = _parse_frontmatter(path)
        results.append(
            Workflow(
                wtype=WorkflowType.AGENT,
                name=path.stem,
                description=meta.get("description", ""),
                path=path,
            )
        )
    return results


def scan_starters() -> list[Starter]:
    """Scan starters/ for starter templates."""
    if not STARTERS_DIR.is_dir():
        return []

    tier_descs = {
        "minimal": "Bare essentials (~20 lines)",
        "standard": "Recommended defaults (~30 lines)",
        "full": "Power user + persona system (~40 lines)",
    }

    results = []
    seen_tiers = set()

    # Check for new consolidated format (minimal.md, standard.md, full.md)
    for tier_name in ("minimal", "standard", "full"):
        path = STARTERS_DIR / f"{tier_name}.md"
        if path.is_file():
            seen_tiers.add(tier_name)
            results.append(
                Starter(
                    tier=tier_name,
                    description=tier_descs.get(tier_name, ""),
                    path=path,
                )
            )

    # Fall back to old paired format (CLAUDE.md.minimal, etc.)
    for path in sorted(STARTERS_DIR.iterdir()):
        if not path.name.startswith("CLAUDE.md."):
            continue
        tier = path.name.split(".")[-1]
        if tier not in seen_tiers:
            results.append(
                Starter(
                    tier=tier,
                    description=tier_descs.get(tier, ""),
                    path=path,
                )
            )

    return results


def scan_personas() -> list[Persona]:
    """Scan starters/personas/ for persona files."""
    personas_dir = STARTERS_DIR / "personas"
    if not personas_dir.is_dir():
        return []

    results = []
    for path in sorted(personas_dir.iterdir()):
        if path.suffix != ".md":
            continue
        if path.name == "_template.md":
            continue
        # Extract tagline from line 3 (blockquote)
        tagline = ""
        try:
            lines = path.read_text().splitlines()
            if len(lines) >= 3:
                line3 = lines[2].lstrip("> ").strip()
                tagline = line3[:50] + "..." if len(line3) > 50 else line3
        except Exception:
            pass
        results.append(
            Persona(name=path.stem, tagline=tagline, path=path)
        )
    return results


def scan_all() -> list[Workflow]:
    """Scan all workflow types."""
    return scan_rules() + scan_skills() + scan_agents()


def validate_rule(path: Path) -> ValidationResult:
    """Validate a single rule file."""
    name = f"rules/{path.stem}"
    meta = _parse_frontmatter(path)
    errors = []
    warnings = []

    if not meta.get("description"):
        warnings.append("Missing 'description' in frontmatter")

    return ValidationResult(workflow_id=name, ok=len(errors) == 0, errors=errors, warnings=warnings)


def validate_skill(skill_dir: Path) -> ValidationResult:
    """Validate a single skill directory."""
    name = f"skills/{skill_dir.name}"
    errors = []
    warnings = []

    skill_file = skill_dir / "SKILL.md"
    if not skill_file.is_file():
        errors.append("Missing SKILL.md")
        return ValidationResult(workflow_id=name, ok=False, errors=errors, warnings=warnings)

    meta = _parse_frontmatter(skill_file)
    if not meta.get("name"):
        warnings.append("Missing 'name' in SKILL.md frontmatter")
    if not meta.get("description"):
        warnings.append("Missing 'description' in SKILL.md frontmatter")

    return ValidationResult(workflow_id=name, ok=len(errors) == 0, errors=errors, warnings=warnings)


def validate_agent(path: Path) -> ValidationResult:
    """Validate a single agent file."""
    name = f"agents/{path.stem}"
    meta = _parse_frontmatter(path)
    errors = []
    warnings = []

    if not meta.get("name"):
        warnings.append("Missing 'name' in frontmatter")
    if not meta.get("description"):
        warnings.append("Missing 'description' in frontmatter")

    return ValidationResult(workflow_id=name, ok=len(errors) == 0, errors=errors, warnings=warnings)


def validate_all(target_path: str | None = None) -> list[ValidationResult]:
    """Validate all workflows (or a specific path)."""
    results = []

    if target_path:
        path = Path(target_path)
        if path.is_file():
            if path.parent.name == "rules":
                results.append(validate_rule(path))
            elif path.parent.name == "agents":
                results.append(validate_agent(path))
            elif path.name == "SKILL.md":
                results.append(validate_skill(path.parent))
        elif path.is_dir():
            results.append(validate_skill(path))
        return results

    # Validate rules
    rules_dir = WORKFLOWS_DIR / "rules"
    if rules_dir.is_dir():
        for path in sorted(rules_dir.iterdir()):
            if path.name == ".gitkeep" or path.suffix not in (".mdc", ".md"):
                continue
            results.append(validate_rule(path))

    # Validate skills
    skills_dir = WORKFLOWS_DIR / "skills"
    if skills_dir.is_dir():
        for skill_dir in sorted(skills_dir.iterdir()):
            if not skill_dir.is_dir():
                continue
            results.append(validate_skill(skill_dir))

    # Validate agents
    agents_dir = WORKFLOWS_DIR / "agents"
    if agents_dir.is_dir():
        for path in sorted(agents_dir.iterdir()):
            if path.name == ".gitkeep" or path.suffix != ".md":
                continue
            results.append(validate_agent(path))

    return results
