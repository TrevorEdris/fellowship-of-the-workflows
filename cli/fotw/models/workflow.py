"""Workflow data models."""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional


class WorkflowType(str, Enum):
    RULE = "rule"
    SKILL = "skill"
    AGENT = "agent"
    STARTER = "starter"
    PERSONA = "persona"

    _PLURAL_MAP: dict[str, str] = {
        "rules": "rule",
        "skills": "skill",
        "agents": "agent",
        "starters": "starter",
        "personas": "persona",
    }

    @classmethod
    def from_str(cls, value: str) -> "WorkflowType":
        """Parse from string, accepting both singular and plural forms."""
        normalized = cls._PLURAL_MAP.get(value, value)
        return cls(normalized)


@dataclass
class Workflow:
    """A single workflow (rule, skill, or agent)."""

    wtype: WorkflowType
    name: str
    description: str = ""
    path: Path = field(default_factory=lambda: Path("."))

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
class ValidationResult:
    """Result of validating a single workflow."""

    workflow_id: str
    ok: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
