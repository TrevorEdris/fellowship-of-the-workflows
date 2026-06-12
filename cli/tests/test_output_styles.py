"""Tests for the deterministic persona output-style generator."""

from pathlib import Path

import frontmatter
import pytest

from fotw.services.catalog import PERSONAS_DIR, REPO_ROOT
from fotw.services.output_styles import (
    OutputStyleError,
    generate_all,
    generate_style,
    parse_spinner_verbs,
    style_filename,
    style_name,
)

OUTPUT_STYLES_DIR = REPO_ROOT / "output-styles"


def _persona_paths() -> list[Path]:
    return sorted(
        p for p in PERSONAS_DIR.glob("*.md") if p.name != "_template.md"
    )


def test_generator_deterministic():
    """Two generation runs over the same persona are byte-identical."""
    for path in _persona_paths():
        assert generate_style(path) == generate_style(path), path.name


def test_generated_frontmatter_invariants():
    """Every generated style has the required frontmatter, and never force-for-plugin."""
    for path in _persona_paths():
        post = frontmatter.loads(generate_style(path))
        assert post.metadata["name"] == style_name(path), path.name
        assert post.metadata["name"].startswith("Persona: "), path.name
        assert post.metadata.get("description"), path.name
        assert post.metadata.get("keep-coding-instructions") is True, path.name
        assert "force-for-plugin" not in post.metadata, path.name


def test_generated_body_self_sufficient():
    """Style bodies must not reference the persona source file (plugin-only
    users do not have personas/ on disk) and must defer to persona.yaml."""
    for path in _persona_paths():
        body = frontmatter.loads(generate_style(path)).content
        assert f"personas/{path.name}" not in body, path.name
        assert ".claude/persona.yaml" in body, path.name
        # The full intensity table is embedded so the runtime read is a lookup
        for level in ("off", "minimal", "noticeable", "excessive"):
            assert level in body, (path.name, level)
        # Boundaries are non-negotiable
        assert "professional voice" in body, path.name


def test_generator_fails_loudly_on_missing_section(tmp_path):
    """A persona missing a required section raises; no partial output."""
    broken = tmp_path / "broken.md"
    broken.write_text(
        "# Persona: Broken\n\n> A persona with almost nothing.\n\n"
        "## Voice Guide\n\n### Speech Patterns\n- only this\n"
    )
    with pytest.raises(OutputStyleError) as exc:
        generate_style(broken)
    assert "broken.md" in str(exc.value)


def test_generator_fails_on_missing_tagline(tmp_path):
    """Line 3 must be the blockquote tagline."""
    broken = tmp_path / "no-tagline.md"
    broken.write_text("# Persona: NoTagline\n\nNot a blockquote\n")
    with pytest.raises(OutputStyleError):
        generate_style(broken)


def test_persona_style_parity():
    """Every persona (excluding the template) has exactly one committed style
    file whose frontmatter name matches, and no orphan style files exist."""
    personas = _persona_paths()
    assert len(personas) >= 14  # 13 original + rocky
    style_files = sorted(OUTPUT_STYLES_DIR.glob("*.md"))
    assert len(style_files) == len(personas)
    for path in personas:
        style_path = OUTPUT_STYLES_DIR / style_filename(path)
        assert style_path.is_file(), f"missing style for {path.name}"
        post = frontmatter.loads(style_path.read_text())
        assert post.metadata["name"] == style_name(path)


def test_committed_styles_are_fresh(tmp_path):
    """Committed output-styles/ must byte-match generator output.

    This is the CI freshness gate: edit a persona -> regenerate via
    `fotw generate output-styles` -> commit, or this test fails.
    """
    generate_all(tmp_path)
    generated = sorted(tmp_path.glob("*.md"))
    committed = sorted(OUTPUT_STYLES_DIR.glob("*.md"))
    assert [p.name for p in generated] == [p.name for p in committed]
    for gen, com in zip(generated, committed):
        assert gen.read_bytes() == com.read_bytes(), (
            f"{com.name} is stale - run `fotw generate output-styles`"
        )


def test_parse_spinner_verbs_all_personas():
    """Every persona ships 10-20 spinner verbs, each <= 25 chars, no
    trailing punctuation, capitalized."""
    for path in _persona_paths():
        verbs = parse_spinner_verbs(path)
        assert 10 <= len(verbs) <= 20, (path.name, len(verbs))
        for verb in verbs:
            assert len(verb) <= 25, (path.name, verb, len(verb))
            assert verb == verb.strip(), (path.name, verb)
            assert verb[0].isupper(), (path.name, verb)
            assert not verb.endswith((".", "!", "?", ",", "…")), (path.name, verb)


def test_parse_spinner_verbs_missing_section(tmp_path):
    broken = tmp_path / "no-verbs.md"
    broken.write_text("# Persona: NoVerbs\n\n> No spinner verbs here.\n")
    with pytest.raises(OutputStyleError):
        parse_spinner_verbs(broken)


def test_rocky_persona_exists():
    """Rocky (Project Hail Mary) is part of the persona roster."""
    rocky = PERSONAS_DIR / "rocky.md"
    assert rocky.is_file()
    text = rocky.read_text()
    assert text.startswith("# Persona: Rocky\n")
    lines = text.splitlines()
    assert lines[2].startswith("> ")  # catalog tagline scrape reads line 3
