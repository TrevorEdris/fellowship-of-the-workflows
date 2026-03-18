"""Translation cache for tool-specific rule files.

Translated rule files are written to ~/.cache/fotw/<tool>/rules/ and symlinked
from the target project. This keeps the fotw repo as the single source of truth:
pulling the repo updates sources, and fotw update regenerates stale cache entries.
"""

from pathlib import Path

from fotw.services.agents import AgentConfig
from fotw.services.frontmatter_translator import translate_content


def get_cache_dir(tool: str) -> Path:
    """Return the cache directory for a given tool."""
    return Path.home() / ".cache" / "fotw" / tool


def get_cache_path(source: Path, wtype: str, cfg: AgentConfig) -> Path:
    """Return the cache path for a translated rule file."""
    target_name = source.stem + cfg.rule_extension
    return get_cache_dir(cfg.name) / wtype / target_name


def is_cache_stale(source: Path, cache_path: Path) -> bool:
    """Return True if the cache file is missing or older than the source."""
    if not cache_path.exists():
        return True
    return source.stat().st_mtime > cache_path.stat().st_mtime


def build_cache_file(source: Path, wtype: str, cfg: AgentConfig) -> Path:
    """Translate source to the cache location and return the cache path."""
    cache_path = get_cache_path(source, wtype, cfg)
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    translated = translate_content(source, cfg.frontmatter_format, cfg.rule_extension)
    cache_path.write_text(translated)
    return cache_path
