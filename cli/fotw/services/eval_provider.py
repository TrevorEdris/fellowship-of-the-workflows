"""LLM provider abstraction for eval runner."""

from dataclasses import dataclass


@dataclass
class ProviderConfig:
    """Configuration for an LLM provider."""
    name: str               # "anthropic", "openai", etc.
    model: str              # "claude-sonnet-4-6", "gpt-4o", etc.
    api_key_env: str        # Environment variable name for API key
    max_tokens: int = 4096
    temperature: float = 0


def get_provider(name: str, model: str | None = None) -> ProviderConfig:
    """Get provider config by name. Model can be overridden."""
    providers = {
        "anthropic": ProviderConfig(
            name="anthropic",
            model=model or "claude-sonnet-4-6",
            api_key_env="ANTHROPIC_API_KEY",
        ),
    }
    if name not in providers:
        raise ValueError(f"Unknown provider: {name}. Available: {', '.join(providers)}")
    cfg = providers[name]
    if model:
        cfg.model = model
    return cfg


JUDGE_SYSTEM_PROMPT = """You are an evaluation judge. Given a skill's output and a rubric, determine if the output passes.

Respond with EXACTLY one of:
- PASS: [one sentence reason]
- FAIL: [one sentence reason]

Do not hedge. Do not say "partially passes". Binary judgment only."""


def build_judge_prompt(output: str, rubric: str) -> str:
    """Build the prompt for the LLM judge."""
    return f"""## Skill Output

{output}

## Rubric

{rubric}

## Judgment

Does the output satisfy the rubric? Respond PASS or FAIL with a one-sentence reason."""
