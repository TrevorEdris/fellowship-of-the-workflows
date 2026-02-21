"""Tests ensuring frontmatter translation works correctly for every rule and every target format.

Source rules are in Cursor format (.mdc). Translation produces:
  - claude:  globs -> paths (array), alwaysApply -> paths: ["**/*"]
  - copilot: globs -> applyTo (string), alwaysApply -> applyTo: "**"
  - generic: description only
  - cursor:  passthrough (no changes)
"""

import frontmatter
import pytest

from fotw.services.catalog import WORKFLOWS_DIR
from fotw.services.frontmatter_translator import translate_content


def _all_rules():
    """Yield (name, path) for every rule file."""
    rules_dir = WORKFLOWS_DIR / "rules"
    if not rules_dir.is_dir():
        return
    for path in sorted(rules_dir.iterdir()):
        if path.suffix not in (".mdc", ".md") or path.name == ".gitkeep":
            continue
        yield path.stem, path


def _parse_translated(content):
    """Parse translated content string into (metadata, body)."""
    post = frontmatter.loads(content)
    return dict(post.metadata), post.content


def _source_meta(path):
    """Parse source file frontmatter."""
    post = frontmatter.load(str(path))
    return dict(post.metadata)


# --- Claude translation ---


@pytest.mark.parametrize("name,path", list(_all_rules()), ids=[n for n, _ in _all_rules()])
def test_translate_to_claude(name, path):
    """Each rule translates to claude format without error."""
    content = translate_content(path, fmt="claude", rule_extension=".md")
    meta, body = _parse_translated(content)
    source = _source_meta(path)

    # Description preserved
    if source.get("description"):
        assert meta.get("description") == source["description"]

    # No cursor-specific fields
    assert "globs" not in meta
    assert "alwaysApply" not in meta

    # If source has globs or alwaysApply, claude must have paths
    if source.get("alwaysApply") or source.get("globs"):
        assert "paths" in meta

    # No .mdc references in body
    assert ".mdc" not in body


# --- Copilot translation ---


@pytest.mark.parametrize("name,path", list(_all_rules()), ids=[n for n, _ in _all_rules()])
def test_translate_to_copilot(name, path):
    """Each rule translates to copilot format without error."""
    content = translate_content(path, fmt="copilot", rule_extension=".instructions.md")
    meta, body = _parse_translated(content)
    source = _source_meta(path)

    # Description preserved
    if source.get("description"):
        assert meta.get("description") == source["description"]

    # No cursor-specific fields
    assert "globs" not in meta
    assert "alwaysApply" not in meta

    # No claude-specific fields
    assert "paths" not in meta

    # If source has globs or alwaysApply, copilot must have applyTo
    if source.get("alwaysApply") or source.get("globs"):
        assert "applyTo" in meta

    # No .mdc references in body
    assert ".mdc" not in body


# --- Generic translation ---


@pytest.mark.parametrize("name,path", list(_all_rules()), ids=[n for n, _ in _all_rules()])
def test_translate_to_generic(name, path):
    """Each rule translates to generic format (description only)."""
    content = translate_content(path, fmt="generic", rule_extension=".md")
    meta, body = _parse_translated(content)
    source = _source_meta(path)

    # Description preserved
    if source.get("description"):
        assert meta.get("description") == source["description"]

    # No file-pattern fields at all
    assert "globs" not in meta
    assert "alwaysApply" not in meta
    assert "paths" not in meta
    assert "applyTo" not in meta


# --- Cursor passthrough ---


@pytest.mark.parametrize("name,path", list(_all_rules()), ids=[n for n, _ in _all_rules()])
def test_translate_to_cursor(name, path):
    """Cursor translation preserves original fields."""
    content = translate_content(path, fmt="cursor", rule_extension=".mdc")
    meta, body = _parse_translated(content)
    source = _source_meta(path)

    # Description preserved
    if source.get("description"):
        assert meta.get("description") == source["description"]

    # Cursor fields preserved if present in source
    if source.get("globs"):
        assert meta.get("globs") == source["globs"]
    if source.get("alwaysApply"):
        assert meta.get("alwaysApply") == source["alwaysApply"]

    # No other-format fields introduced
    assert "paths" not in meta
    assert "applyTo" not in meta


# --- Body content preservation ---


@pytest.mark.parametrize("name,path", list(_all_rules()), ids=[n for n, _ in _all_rules()])
def test_translation_preserves_body_content(name, path):
    """Translation preserves body content (modulo extension replacements)."""
    source_post = frontmatter.load(str(path))
    source_body = source_post.content

    translated = translate_content(path, fmt="claude", rule_extension=".md")
    _, translated_body = _parse_translated(translated)

    # After normalizing .mdc -> .md, bodies should match
    normalized_source = source_body.replace(".mdc", ".md")
    assert normalized_source.strip() == translated_body.strip()
