"""Agent target configuration — defines how each AI tool receives installed files."""

from dataclasses import dataclass


@dataclass(frozen=True)
class AgentConfig:
    """Configuration for a specific AI tool target."""

    name: str
    # Directory for rules/skills/agents
    config_dir: str  # e.g., ".claude", ".cursor", ".github/copilot"
    # Starter file name
    starter_filename: str  # e.g., "CLAUDE.md", "AGENTS.md"
    # Rule file extension
    rule_extension: str  # e.g., ".md", ".mdc", ".instructions.md"
    # Frontmatter format
    frontmatter_format: str  # "claude", "cursor", "copilot", "generic"
    # Whether this agent supports skills directory
    supports_skills: bool = True
    # Whether this agent supports agents directory
    supports_agents: bool = True
    # Rules subdirectory name (relative to config_dir)
    rules_subdir: str = "rules"
    # Skills subdirectory name
    skills_subdir: str = "skills"
    # Agents subdirectory name
    agents_subdir: str = "agents"


# Tier 1 agents — well-known, tested configurations
TIER_1_AGENTS: dict[str, AgentConfig] = {
    "claude-code": AgentConfig(
        name="Claude Code",
        config_dir=".claude",
        starter_filename="CLAUDE.md",
        rule_extension=".md",
        frontmatter_format="claude",
    ),
    "cursor": AgentConfig(
        name="Cursor",
        config_dir=".cursor",
        starter_filename="AGENTS.md",
        rule_extension=".mdc",
        frontmatter_format="cursor",
    ),
    "copilot": AgentConfig(
        name="GitHub Copilot",
        config_dir=".github",
        starter_filename="AGENTS.md",
        rule_extension=".instructions.md",
        frontmatter_format="copilot",
        rules_subdir="instructions",
        supports_agents=False,
    ),
    "codex": AgentConfig(
        name="OpenAI Codex",
        config_dir=".codex",
        starter_filename="AGENTS.md",
        rule_extension=".md",
        frontmatter_format="generic",
        supports_agents=False,
    ),
}

# Tier 2 agents — community/experimental
TIER_2_AGENTS: dict[str, AgentConfig] = {
    "windsurf": AgentConfig(
        name="Windsurf",
        config_dir=".windsurf",
        starter_filename="AGENTS.md",
        rule_extension=".md",
        frontmatter_format="generic",
        rules_subdir="rules",
    ),
    "roo": AgentConfig(
        name="Roo Code",
        config_dir=".roo",
        starter_filename="AGENTS.md",
        rule_extension=".md",
        frontmatter_format="generic",
    ),
    "gemini": AgentConfig(
        name="Gemini Code Assist",
        config_dir=".gemini",
        starter_filename="AGENTS.md",
        rule_extension=".md",
        frontmatter_format="generic",
    ),
    "goose": AgentConfig(
        name="Goose",
        config_dir=".goose",
        starter_filename="AGENTS.md",
        rule_extension=".md",
        frontmatter_format="generic",
        supports_agents=False,
    ),
    "universal": AgentConfig(
        name="Universal",
        config_dir=".ai",
        starter_filename="AGENTS.md",
        rule_extension=".md",
        frontmatter_format="generic",
    ),
}

ALL_AGENTS: dict[str, AgentConfig] = {**TIER_1_AGENTS, **TIER_2_AGENTS}

# Special pseudo-target
BOTH_TARGET = "both"  # Installs for both claude-code and cursor


def expand_tools(tool: str) -> list[str]:
    """Expand a tool target (including 'both') into a list of real agent names."""
    if tool == BOTH_TARGET:
        return ["claude-code", "cursor"]
    return [tool]


def get_agent_config(tool: str) -> AgentConfig | None:
    """Look up agent configuration by tool name."""
    return ALL_AGENTS.get(tool)


def is_valid_tool(tool: str) -> bool:
    """Check if a tool name is recognized."""
    return tool in ALL_AGENTS or tool == BOTH_TARGET


def list_tools() -> list[str]:
    """Return all valid tool names."""
    return sorted(ALL_AGENTS.keys())
