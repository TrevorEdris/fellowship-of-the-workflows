"""Translate frontmatter between tool formats (Cursor .mdc <-> Claude .md)."""

from pathlib import Path

import frontmatter


def _translate_post(source: Path) -> frontmatter.Post:
    """Parse source and return a new Post with Claude-format metadata.

    Converts:
    - globs -> paths (as array)
    - alwaysApply: true -> paths: ["**/*"]
    - Removes globs, alwaysApply fields
    """
    post = frontmatter.load(str(source))

    description = post.metadata.get("description", "")
    globs = post.metadata.get("globs", "")
    always_apply = post.metadata.get("alwaysApply", False)

    new_meta: dict = {}
    if description:
        new_meta["description"] = description

    if always_apply or globs == "**/*":
        new_meta["paths"] = ["**/*"]
    elif globs:
        new_meta["paths"] = [f"**/{globs}"]

    return frontmatter.Post(post.content, **new_meta)


def translate_to_claude(source: Path, target: Path) -> None:
    """Translate a Cursor .mdc rule to Claude .md format and write to target."""
    new_post = _translate_post(source)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(frontmatter.dumps(new_post) + "\n")


def translate_content(source: Path) -> str:
    """Return translated content as a string (for diff comparison)."""
    new_post = _translate_post(source)
    return frontmatter.dumps(new_post) + "\n"
