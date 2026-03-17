"""Workflow data models."""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional


VALID_TAGS: frozenset[str] = frozenset({
    "aws",
    "azure",
    "gcp",
    "go",
    "python",
    "typescript",
    "rust",
    "infrastructure",
    "review",
    "documentation",
    "architecture",
    "meta",
    "incident-response",
    "security",
    "testing",
    "observability",
    "ci-cd",
    "git",
})


class WorkflowType(str, Enum):
    RULE = "rule"
    SKILL = "skill"
    AGENT = "agent"
    STARTER = "starter"
    PERSONA = "persona"
    HOOK = "hook"
    ROLE = "role"

    @classmethod
    def from_str(cls, value: str) -> "WorkflowType":
        """Parse from string, accepting both singular and plural forms."""
        normalized = _PLURAL_MAP.get(value, value)
        return cls(normalized)


_PLURAL_MAP: dict[str, str] = {
    "rules": "rule",
    "skills": "skill",
    "agents": "agent",
    "starters": "starter",
    "personas": "persona",
    "hooks": "hook",
    "roles": "role",
    "rosters": "role",
}


@dataclass
class Workflow:
    """A single workflow (rule, skill, or agent)."""

    wtype: WorkflowType
    name: str
    description: str = ""
    path: Path = field(default_factory=lambda: Path("."))
    tags: list[str] = field(default_factory=list)
    tier: str = "core"  # "core" or "community"

    @property
    def workflow_id(self) -> str:
        return f"{self.wtype.value}s/{self.name}"


@dataclass
class Starter:
    """A starter template."""

    tier: str
    description: str = ""
    path: Path = field(default_factory=lambda: Path("."))


@dataclass
class Persona:
    """A persona definition."""

    name: str
    tagline: str = ""
    path: Path = field(default_factory=lambda: Path("."))


@dataclass
class Role:
    """A role definition from the roster."""

    name: str
    description: str = ""
    tags: list[str] = field(default_factory=list)
    allowed_skills: list[str] = field(default_factory=list)
    denied_skills: list[str] = field(default_factory=list)
    preferred_model: str = ""
    rules: list[str] = field(default_factory=list)
    persona: str = ""
    path: Path = field(default_factory=lambda: Path("."))

    @property
    def workflow_id(self) -> str:
        return f"rosters/{self.name}"


@dataclass
class Hook:
    """A Claude Code hook script."""

    name: str
    description: str
    event: str
    matcher: str
    path: Path = field(default_factory=lambda: Path("."))
    has_tests: bool = False

    @property
    def workflow_id(self) -> str:
        return f"hooks/{self.name}"

    @property
    def settings_entry(self) -> dict:
        """Build a settings.json hook entry fragment."""
        entry: dict = {
            "hooks": [
                {
                    "type": "command",
                    "command": f"node ~/.claude/hooks/{self.name}.js",
                }
            ],
        }
        if self.matcher:
            entry["matcher"] = self.matcher
        return entry


@dataclass
class ValidationResult:
    """Result of validating a single workflow."""

    workflow_id: str
    ok: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
