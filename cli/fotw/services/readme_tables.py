"""Generate the Skill Tags and Skills by Category sections for README.md."""

import re
import sys
from collections import defaultdict
from pathlib import Path

from fotw.models.workflow import VALID_TAGS
from fotw.services.catalog import REPO_ROOT, scan_skills

# Tag descriptions — single source of truth for README generation
TAG_DESCRIPTIONS: dict[str, str] = {
    "infrastructure": "IaC, provisioning, containers, cloud resources",
    "architecture": "System design, API design, patterns, databases",
    "review": "Code, design, security, or performance review",
    "documentation": "Docs generation, writing, diagrams",
    "meta": "Agent self-management, session tools, orchestration",
    "incident-response": "Alerting, on-call, incident management",
    "aws": "Amazon Web Services",
    "gcp": "Google Cloud Platform",
    "azure": "Microsoft Azure",
    "security": "Security hardening, IAM, vulnerability analysis",
    "testing": "TDD, E2E, test scaffolding, debugging",
    "observability": "Monitoring instrumentation, dashboards, SLOs",
    "ci-cd": "CI/CD pipelines, deployment automation",
    "git": "Git workflows, branching, PRs, commits",
    "go": "Go language patterns",
    "python": "Python language patterns",
    "typescript": "TypeScript language patterns",
    "rust": "Rust language patterns",
}

# Category grouping for "Skills by Category" (order matters for display)
CATEGORY_ORDER = [
    "Infrastructure",
    "Architecture",
    "Review",
    "Documentation",
    "Meta",
    "Incident Response",
    "Cloud Platforms",
    "Security",
    "Testing",
    "Observability",
    "Other",
]

# Map display category → tags that belong in it
CATEGORY_TAGS: dict[str, list[str]] = {
    "Infrastructure": ["infrastructure"],
    "Architecture": ["architecture"],
    "Review": ["review"],
    "Documentation": ["documentation"],
    "Meta": ["meta"],
    "Incident Response": ["incident-response"],
    "Cloud Platforms": ["aws", "azure", "gcp"],
    "Security": ["security"],
    "Testing": ["testing"],
    "Observability": ["observability"],
    "Other": ["ci-cd", "git", "go", "python", "typescript", "rust"],
}


def _truncate(text: str, max_len: int = 55) -> str:
    if len(text) > max_len:
        return text[: max_len - 3] + "..."
    return text


def generate_tables() -> str:
    """Generate the Skill Tags + Skills by Category markdown sections."""
    skills = scan_skills()

    # Count tags
    tag_counts: dict[str, int] = defaultdict(int)
    for skill in skills:
        for tag in skill.tags:
            tag_counts[tag] += 1

    # Sort by count descending, then alphabetically
    sorted_tags = sorted(tag_counts.keys(), key=lambda t: (-tag_counts[t], t))

    lines: list[str] = []

    # --- Tag Reference ---
    lines.append("### Skill Tags")
    lines.append("")
    lines.append("Skills are categorized with tags for filtering. Use `./bin/fotw list --tag <tag>` to filter.")
    lines.append("")
    lines.append("| Tag | Description | Count |")
    lines.append("|-----|-------------|-------|")
    for tag in sorted_tags:
        desc = TAG_DESCRIPTIONS.get(tag, "")
        lines.append(f"| `{tag}` | {desc} | {tag_counts[tag]} |")
    lines.append("")

    # --- Skills by Category (inside <details>) ---
    lines.append("<details>")
    lines.append('<summary><strong>Skills by Category</strong> (click to expand)</summary>')
    lines.append("")

    # Build category → skills mapping
    categorized: dict[str, list] = {cat: [] for cat in CATEGORY_ORDER}
    for skill in skills:
        placed = False
        for cat, cat_tags in CATEGORY_TAGS.items():
            if any(t in cat_tags for t in skill.tags):
                categorized[cat].append(skill)
                placed = True
        if not placed and skill.tags:
            categorized["Other"].append(skill)

    for cat in CATEGORY_ORDER:
        cat_skills = categorized[cat]
        if not cat_skills:
            continue
        # Deduplicate (skills with multiple matching tags)
        seen = set()
        unique = []
        for s in sorted(cat_skills, key=lambda s: s.name):
            if s.name not in seen:
                seen.add(s.name)
                unique.append(s)

        lines.append(f"#### {cat}")
        lines.append("")
        lines.append("| Skill | Tags | Description |")
        lines.append("|-------|------|-------------|")
        for s in unique:
            tags_str = "`, `".join(s.tags)
            lines.append(f"| `{s.name}` | `{tags_str}` | {_truncate(s.description)} |")
        lines.append("")

    lines.append("</details>")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    """CLI entry point for bin/generate-readme-tables."""
    update = "--update" in sys.argv

    content = generate_tables()

    if not update:
        print(content)
        return

    readme_path = REPO_ROOT / "README.md"
    readme = readme_path.read_text()

    # Replace between "### Skill Tags" and "### Hooks (Claude Code only)"
    # Handles both flat and <details>-wrapped category sections
    pattern = r"### Skill Tags\n.*?(?=### Hooks \(Claude Code only\))"
    new_readme, count = re.subn(pattern, content + "\n", readme, flags=re.DOTALL)

    if count == 0:
        print("Error: Could not find '### Skill Tags' ... '### Hooks' markers in README.md", file=sys.stderr)
        sys.exit(1)

    readme_path.write_text(new_readme)
    print(f"Updated README.md skill tables ({readme_path})")
