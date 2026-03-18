"""Scan and parse the workflow catalog from disk."""

import json
import os
import re
from pathlib import Path

import frontmatter

from fotw.models.workflow import (
    Hook,
    Persona,
    Role,
    Starter,
    ValidationResult,
    Workflow,
    WorkflowType,
)


def _repo_root() -> Path:
    """Find the repository root (parent of cli/).

    Supports FOTW_REPO_ROOT env var for testing and non-standard layouts.
    """
    env_root = os.environ.get("FOTW_REPO_ROOT")
    if env_root:
        return Path(env_root).resolve()

    here = Path(__file__).resolve()
    # Walk up until we find bin/ + .claude-plugin/ (repo root marker)
    for parent in here.parents:
        if (parent / "bin").is_dir() and (parent / ".claude-plugin").is_dir():
            return parent
    raise RuntimeError("Cannot locate repository root")


REPO_ROOT = _repo_root()
# After the plugin-first flatten, workflows live at repo root.
# WORKFLOWS_DIR is kept as a backward-compatible alias used by tests and other modules.
WORKFLOWS_DIR = REPO_ROOT
LANGUAGES_DIR = REPO_ROOT / "languages"
PLATFORMS_DIR = REPO_ROOT / "platforms"
VENDORS_DIR = REPO_ROOT / "vendors"

# Ordered lists of (dir, tier) for each workflow type
_EXTRA_SKILL_DIRS: list[tuple] = [
    (LANGUAGES_DIR / "skills", "languages"),
    (PLATFORMS_DIR / "skills", "platforms"),
    (VENDORS_DIR / "skills", "vendors"),
]
_EXTRA_RULE_DIRS: list[tuple] = [
    (LANGUAGES_DIR / "rules", "languages"),
    (PLATFORMS_DIR / "rules", "platforms"),
    (VENDORS_DIR / "rules", "vendors"),
]
_EXTRA_AGENT_DIRS: list[tuple] = [
    (PLATFORMS_DIR / "agents", "platforms"),
    (VENDORS_DIR / "agents", "vendors"),
]

STARTERS_DIR = REPO_ROOT / "starters"
ROSTERS_DIR = STARTERS_DIR / "rosters"


def _parse_frontmatter(path: Path) -> dict:
    """Parse YAML frontmatter from a markdown file."""
    try:
        post = frontmatter.load(str(path))
        return dict(post.metadata)
    except Exception:
        return {}


def scan_rules() -> list[Workflow]:
    """Scan rules/ and language/platform/vendor rule dirs for rule files."""
    results = []
    for base_dir, tier in [(WORKFLOWS_DIR / "rules", "core")] + _EXTRA_RULE_DIRS:
        if not base_dir.is_dir():
            continue
        for path in sorted(base_dir.iterdir()):
            if path.name == ".gitkeep":
                continue
            if path.suffix not in (".mdc", ".md"):
                continue
            meta = _parse_frontmatter(path)
            tags = meta.get("tags", [])
            if isinstance(tags, str):
                tags = [t.strip() for t in tags.split(",")]
            results.append(
                Workflow(
                    wtype=WorkflowType.RULE,
                    name=path.stem,
                    description=meta.get("description", ""),
                    path=path,
                    tags=tags,
                    tier=tier,
                )
            )
    return results


def scan_skills() -> list[Workflow]:
    """Scan skills/ and language/platform/vendor skill dirs for skill directories."""
    results = []
    for base_dir, tier in [(WORKFLOWS_DIR / "skills", "core")] + _EXTRA_SKILL_DIRS:
        if not base_dir.is_dir():
            continue
        for skill_dir in sorted(base_dir.iterdir()):
            if not skill_dir.is_dir():
                continue
            skill_file = skill_dir / "SKILL.md"
            if not skill_file.is_file():
                continue
            meta = _parse_frontmatter(skill_file)
            tags = meta.get("tags", [])
            if isinstance(tags, str):
                tags = [t.strip() for t in tags.split(",")]
            results.append(
                Workflow(
                    wtype=WorkflowType.SKILL,
                    name=skill_dir.name,
                    description=meta.get("description", ""),
                    path=skill_dir,
                    tags=tags,
                    tier=tier,
                )
            )
    return results


def scan_agents() -> list[Workflow]:
    """Scan agents/ and platform/vendor agent dirs for agent files."""
    results = []
    for base_dir, tier in [(WORKFLOWS_DIR / "agents", "core")] + _EXTRA_AGENT_DIRS:
        if not base_dir.is_dir():
            continue
        for path in sorted(base_dir.iterdir()):
            if path.name == ".gitkeep":
                continue
            if path.suffix != ".md":
                continue
            meta = _parse_frontmatter(path)
            tags = meta.get("tags", [])
            if isinstance(tags, str):
                tags = [t.strip() for t in tags.split(",")]
            results.append(
                Workflow(
                    wtype=WorkflowType.AGENT,
                    name=path.stem,
                    description=meta.get("description", ""),
                    path=path,
                    tags=tags,
                    tier=tier,
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


def scan_roles() -> list[Role]:
    """Scan starters/rosters/ for role definitions."""
    if not ROSTERS_DIR.is_dir():
        return []

    results = []
    for path in sorted(ROSTERS_DIR.iterdir()):
        if path.suffix != ".md":
            continue
        if path.name == "README.md":
            continue
        meta = _parse_frontmatter(path)
        tags = meta.get("tags", [])
        if isinstance(tags, str):
            tags = [t.strip() for t in tags.split(",")]
        allowed_skills = meta.get("allowed-skills", [])
        if isinstance(allowed_skills, str):
            allowed_skills = [s.strip() for s in allowed_skills.split(",")]
        denied_skills = meta.get("denied-skills", [])
        if isinstance(denied_skills, str):
            denied_skills = [s.strip() for s in denied_skills.split(",")]
        rules = meta.get("rules", [])
        if isinstance(rules, str):
            rules = [r.strip() for r in rules.split(",")]
        results.append(
            Role(
                name=path.stem,
                description=meta.get("description", ""),
                tags=tags,
                allowed_skills=allowed_skills,
                denied_skills=denied_skills,
                preferred_model=meta.get("preferred-model", ""),
                rules=rules,
                persona=meta.get("persona", ""),
                path=path,
            )
        )
    return results


KNOWN_HOOK_EVENTS = {"PreToolUse", "PostToolUse", "PreCompact", "PostCompact",
                      "UserPromptSubmit", "Stop", "SubagentStop"}

_HOOK_META_RE = re.compile(r'@fotw-hook\s*(\{[^}]+\})')


def _parse_hook_meta(path: Path) -> dict | None:
    """Extract @fotw-hook JSON metadata from a .js file."""
    try:
        content = path.read_text()
    except Exception:
        return None
    m = _HOOK_META_RE.search(content)
    if not m:
        return None
    try:
        return json.loads(m.group(1))
    except json.JSONDecodeError:
        return None


def scan_hooks() -> list[Hook]:
    """Scan hooks/ for hook scripts with @fotw-hook metadata."""
    hooks_dir = WORKFLOWS_DIR / "hooks"
    if not hooks_dir.is_dir():
        return []

    tests_dir = hooks_dir / "tests"
    results = []
    for path in sorted(hooks_dir.iterdir()):
        if path.suffix != ".js":
            continue
        meta = _parse_hook_meta(path)
        if not meta:
            continue
        # Check for tests
        has_tests = False
        if tests_dir.is_dir():
            test_file = f"{path.stem}.test.js"
            for sub in tests_dir.iterdir():
                if sub.is_dir() and (sub / test_file).is_file():
                    has_tests = True
                    break
        results.append(
            Hook(
                name=path.stem,
                description=meta.get("description", ""),
                event=meta.get("event", ""),
                matcher=meta.get("matcher", ""),
                path=path,
                has_tests=has_tests,
            )
        )
    return results


def validate_hook(path: Path) -> ValidationResult:
    """Validate a single hook script."""
    name = f"hooks/{path.stem}"
    errors = []
    warnings = []

    try:
        content = path.read_text()
    except Exception as e:
        errors.append(f"Cannot read file: {e}")
        return ValidationResult(workflow_id=name, ok=False, errors=errors, warnings=warnings)

    if not content.startswith("#!/usr/bin/env node"):
        warnings.append("Missing shebang (#!/usr/bin/env node)")

    meta = _parse_hook_meta(path)
    if not meta:
        errors.append("Missing or invalid @fotw-hook metadata")
        return ValidationResult(workflow_id=name, ok=False, errors=errors, warnings=warnings)

    event = meta.get("event", "")
    if not event:
        errors.append("@fotw-hook missing 'event' field")
    elif event not in KNOWN_HOOK_EVENTS:
        warnings.append(f"Unknown hook event: {event}")

    if not meta.get("description"):
        warnings.append("Missing 'description' in @fotw-hook metadata")

    return ValidationResult(workflow_id=name, ok=len(errors) == 0, errors=errors, warnings=warnings)


def scan_all() -> list[Workflow]:
    """Scan all workflow types."""
    return scan_rules() + scan_skills() + scan_agents()


def filter_workflows(
    workflows: list[Workflow],
    type_filter: str | None = None,
    tier_filter: str | None = None,
    tags: list[str] | None = None,
) -> list[Workflow]:
    """Filter workflows by type, tier, and/or tags (AND logic)."""
    result = workflows
    if type_filter:
        result = [wf for wf in result if wf.wtype.value == type_filter]
    if tier_filter:
        result = [wf for wf in result if wf.tier == tier_filter]
    if tags:
        result = [wf for wf in result if all(t in wf.tags for t in tags)]
    return result


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

    # Least-privilege check on allowed-tools
    allowed_tools = meta.get("allowed-tools", "")
    if isinstance(allowed_tools, str):
        _check_tool_scoping(allowed_tools, warnings)

    return ValidationResult(workflow_id=name, ok=len(errors) == 0, errors=errors, warnings=warnings)


# Wildcards that grant overly broad access
_OVERLY_BROAD_PATTERNS = [
    ("Bash(git:*)", "Use specific git subcommands: Bash(git diff:*), Bash(git log:*), etc."),
    ("Bash(gh:*)", "Use specific gh subcommands: Bash(gh pr view:*), Bash(gh pr diff:*), etc."),
]


def _check_tool_scoping(allowed_tools: str, warnings: list[str]) -> None:
    """Warn on overly broad Bash scoping patterns."""
    for pattern, suggestion in _OVERLY_BROAD_PATTERNS:
        if pattern in allowed_tools:
            warnings.append(
                f"Overly broad tool scope: '{pattern}' grants access to destructive commands. "
                f"{suggestion}"
            )


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


def validate_role(path: Path) -> ValidationResult:
    """Validate a single role definition."""
    name = f"rosters/{path.stem}"
    meta = _parse_frontmatter(path)
    errors = []
    warnings = []

    if not meta.get("name"):
        warnings.append("Missing 'name' in frontmatter")
    if not meta.get("description"):
        warnings.append("Missing 'description' in frontmatter")
    if not meta.get("allowed-skills"):
        errors.append("Missing 'allowed-skills' in frontmatter (a role must include at least one skill)")

    # Validate allowed-skills reference real skills (core or language/platform/vendor)
    allowed = meta.get("allowed-skills", [])
    if isinstance(allowed, str):
        allowed = [s.strip() for s in allowed.split(",")]
    skills_dir = WORKFLOWS_DIR / "skills"
    extra_skill_dirs = [d for d, _ in _EXTRA_SKILL_DIRS]
    for skill_name in allowed:
        exists = (skills_dir / skill_name).is_dir() or any(
            (d / skill_name).is_dir() for d in extra_skill_dirs
        )
        if not exists:
            warnings.append(f"allowed-skills references non-existent skill: {skill_name}")

    # Validate rules reference real rules (core or language/platform/vendor)
    rules = meta.get("rules", [])
    if isinstance(rules, str):
        rules = [r.strip() for r in rules.split(",")]
    rules_dir = WORKFLOWS_DIR / "rules"
    extra_rule_dirs = [d for d, _ in _EXTRA_RULE_DIRS]
    for rule_name in rules:
        exists = (
            (rules_dir / f"{rule_name}.mdc").is_file()
            or (rules_dir / f"{rule_name}.md").is_file()
            or any(
                (d / f"{rule_name}.mdc").is_file() or (d / f"{rule_name}.md").is_file()
                for d in extra_rule_dirs
            )
        )
        if not exists:
            warnings.append(f"rules references non-existent rule: {rule_name}")

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

    # Validate rules (core + language/platform/vendor)
    for rules_base, _ in [(WORKFLOWS_DIR / "rules", "core")] + _EXTRA_RULE_DIRS:
        if rules_base.is_dir():
            for path in sorted(rules_base.iterdir()):
                if path.name == ".gitkeep" or path.suffix not in (".mdc", ".md"):
                    continue
                results.append(validate_rule(path))

    # Validate skills (core + language/platform/vendor)
    for base_dir, _ in [(WORKFLOWS_DIR / "skills", "core")] + _EXTRA_SKILL_DIRS:
        if base_dir.is_dir():
            for skill_dir in sorted(base_dir.iterdir()):
                if not skill_dir.is_dir():
                    continue
                results.append(validate_skill(skill_dir))

    # Validate agents (core + platform/vendor)
    for agents_base, _ in [(WORKFLOWS_DIR / "agents", "core")] + _EXTRA_AGENT_DIRS:
        if agents_base.is_dir():
            for path in sorted(agents_base.iterdir()):
                if path.name == ".gitkeep" or path.suffix != ".md":
                    continue
                results.append(validate_agent(path))

    # Validate hooks
    hooks_dir = WORKFLOWS_DIR / "hooks"
    if hooks_dir.is_dir():
        for path in sorted(hooks_dir.iterdir()):
            if path.suffix != ".js":
                continue
            results.append(validate_hook(path))

    # Validate roles
    if ROSTERS_DIR.is_dir():
        for path in sorted(ROSTERS_DIR.iterdir()):
            if path.suffix != ".md" or path.name == "README.md":
                continue
            results.append(validate_role(path))

    return results
