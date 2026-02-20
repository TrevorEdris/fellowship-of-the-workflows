"""Translate frontmatter between tool formats.

Source rules are stored in Cursor format (.mdc with globs/alwaysApply).
Translation handles: Cursor, Claude, Copilot, and generic formats.
"""

from pathlib import Path

import frontmatter


def _parse_source(source: Path) -> tuple[dict, str]:
    """Parse source file and return (metadata, body content)."""
    post = frontmatter.load(str(source))
    return dict(post.metadata), post.content


def _translate_meta(meta: dict, fmt: str) -> dict:
    """Translate source metadata to the target format.

    Source format (Cursor .mdc):
        description, globs, alwaysApply

    Target formats:
        claude:  description, paths (array)
        cursor:  description, globs, alwaysApply (passthrough)
        copilot: description, applyTo (string)
        generic: description only (no file-pattern fields)
    """
    description = meta.get("description", "")
    globs = meta.get("globs", "")
    always_apply = meta.get("alwaysApply", False)

    new_meta: dict = {}
    if description:
        new_meta["description"] = description

    if fmt == "cursor":
        # Passthrough — keep original fields
        if globs:
            new_meta["globs"] = globs
        if always_apply:
            new_meta["alwaysApply"] = always_apply
    elif fmt == "claude":
        if always_apply or globs == "**/*":
            new_meta["paths"] = ["**/*"]
        elif globs:
            parts = [g.strip() for g in str(globs).split(",") if g.strip()]
            new_meta["paths"] = [f"**/{g}" for g in parts]
    elif fmt == "copilot":
        if always_apply or globs == "**/*":
            new_meta["applyTo"] = "**"
        elif globs:
            new_meta["applyTo"] = globs
    # generic: description only

    return new_meta


def _translate_body(content: str, rule_extension: str) -> str:
    """Replace .mdc file references in body with the target rule extension."""
    if rule_extension == ".mdc":
        return content
    return content.replace(".mdc", rule_extension)


def translate_to_target(
    source: Path, target: Path, fmt: str, rule_extension: str = ".md"
) -> None:
    """Translate a rule file to the target format and write to target path."""
    meta, content = _parse_source(source)
    new_meta = _translate_meta(meta, fmt)
    new_post = frontmatter.Post(_translate_body(content, rule_extension), **new_meta)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(frontmatter.dumps(new_post) + "\n")


def translate_content(
    source: Path, fmt: str = "claude", rule_extension: str = ".md"
) -> str:
    """Return translated content as a string (for diff comparison)."""
    meta, content = _parse_source(source)
    new_meta = _translate_meta(meta, fmt)
    new_post = frontmatter.Post(_translate_body(content, rule_extension), **new_meta)
    return frontmatter.dumps(new_post) + "\n"


