"""Tests for the install command and installer service."""

import shutil
from pathlib import Path

import pytest

from fotw.services.frontmatter_translator import translate_content
from fotw.services.installer import (
    InstallContext,
    install_all,
    install_personas,
    install_single_workflow,
    install_starter,
)
from fotw.services.catalog import WORKFLOWS_DIR, STARTERS_DIR
from fotw.ui.diff import files_are_identical


@pytest.fixture
def tmp_target(tmp_path: Path) -> Path:
    """Create a temporary target directory."""
    target = tmp_path / "test-project"
    target.mkdir()
    return target


# --- Frontmatter translation ---


def test_translate_content_always_apply():
    """Rules with alwaysApply: true get paths: ['**/*']."""
    rule = WORKFLOWS_DIR / "rules" / "git-safety.mdc"
    if not rule.exists():
        pytest.skip("git-safety.mdc not found")
    content = translate_content(rule)
    assert "paths:" in content
    assert "**/*" in content
    assert "alwaysApply" not in content
    assert "globs" not in content


def test_translate_content_preserves_description():
    """Translation preserves the description field."""
    rule = WORKFLOWS_DIR / "rules" / "ai-session.mdc"
    if not rule.exists():
        pytest.skip("ai-session.mdc not found")
    content = translate_content(rule)
    assert "description:" in content


# --- Single workflow install ---


def test_install_rule_claude(tmp_target: Path):
    """Install a rule for claude-code creates .claude/rules/<name>.md."""
    ctx = InstallContext(tool="claude-code", target_repo=tmp_target, force=True, quiet=True)
    assert install_single_workflow("rules/ai-session", ctx)
    target = tmp_target / ".claude" / "rules" / "ai-session.md"
    assert target.is_file()
    content = target.read_text()
    assert "paths:" in content  # Frontmatter was translated


def test_install_rule_cursor(tmp_target: Path):
    """Install a rule for cursor creates .cursor/rules/<name>.mdc."""
    ctx = InstallContext(tool="cursor", target_repo=tmp_target, force=True, quiet=True)
    assert install_single_workflow("rules/ai-session", ctx)
    target = tmp_target / ".cursor" / "rules" / "ai-session.mdc"
    assert target.is_file()
    content = target.read_text()
    assert "globs:" in content or "alwaysApply:" in content  # Original frontmatter


def test_install_skill(tmp_target: Path):
    """Install a skill copies the entire directory."""
    ctx = InstallContext(tool="claude-code", target_repo=tmp_target, force=True, quiet=True)
    assert install_single_workflow("skills/code-review", ctx)
    target_dir = tmp_target / ".claude" / "skills" / "code-review"
    assert target_dir.is_dir()
    assert (target_dir / "SKILL.md").is_file()


def test_install_agent(tmp_target: Path):
    """Install an agent copies the file."""
    ctx = InstallContext(tool="claude-code", target_repo=tmp_target, force=True, quiet=True)
    assert install_single_workflow("agents/pragmatic-code-review", ctx)
    target = tmp_target / ".claude" / "agents" / "pragmatic-code-review.md"
    assert target.is_file()


def test_install_nonexistent_fails(tmp_target: Path):
    """Installing a nonexistent workflow returns False."""
    ctx = InstallContext(tool="claude-code", target_repo=tmp_target, force=True, quiet=True)
    assert not install_single_workflow("rules/nonexistent", ctx)


# --- Conflict resolution ---


def test_install_force_overwrites(tmp_target: Path):
    """--force overwrites existing files."""
    rules_dir = tmp_target / ".claude" / "rules"
    rules_dir.mkdir(parents=True)
    target = rules_dir / "ai-session.md"
    target.write_text("# Custom content\n")

    ctx = InstallContext(tool="claude-code", target_repo=tmp_target, force=True, quiet=True)
    assert install_single_workflow("rules/ai-session", ctx)

    content = target.read_text()
    assert "# Custom content" not in content  # Overwritten


def test_install_identical_skips(tmp_target: Path):
    """Identical files are detected and skipped."""
    # First install
    ctx = InstallContext(tool="claude-code", target_repo=tmp_target, force=True, quiet=True)
    install_single_workflow("rules/ai-session", ctx)

    target = tmp_target / ".claude" / "rules" / "ai-session.md"
    content1 = target.read_text()

    # Second install without force — should skip silently (identical)
    ctx2 = InstallContext(tool="claude-code", target_repo=tmp_target, force=False, quiet=True)
    assert install_single_workflow("rules/ai-session", ctx2)
    content2 = target.read_text()
    assert content1 == content2


# --- Dry run ---


def test_dry_run_no_files(tmp_target: Path):
    """--dry-run produces no file changes."""
    ctx = InstallContext(tool="claude-code", target_repo=tmp_target, dry_run=True, quiet=True)
    assert install_single_workflow("rules/ai-session", ctx)
    rules_dir = tmp_target / ".claude" / "rules"
    assert not rules_dir.exists()


# --- Starters ---


def test_install_starter_minimal_claude(tmp_target: Path):
    """Minimal starter creates CLAUDE.md and bundles 2 rules."""
    ctx = InstallContext(tool="claude-code", target_repo=tmp_target, force=True)
    assert install_starter("minimal", ctx)
    assert (tmp_target / "CLAUDE.md").is_file()
    assert (tmp_target / ".claude" / "rules" / "git-safety.md").is_file()
    assert (tmp_target / ".claude" / "rules" / "output-style.md").is_file()


def test_install_starter_standard_cursor(tmp_target: Path):
    """Standard starter creates AGENTS.md and bundles 4 rules."""
    ctx = InstallContext(tool="cursor", target_repo=tmp_target, force=True)
    assert install_starter("standard", ctx)
    assert (tmp_target / "AGENTS.md").is_file()
    rules_dir = tmp_target / ".cursor" / "rules"
    assert (rules_dir / "git-safety.mdc").is_file()
    assert (rules_dir / "discover-plan-implement.mdc").is_file()
    assert (rules_dir / "ai-session.mdc").is_file()


def test_install_starter_full_claude(tmp_target: Path):
    """Full starter bundles all 6 rules and personas."""
    ctx = InstallContext(tool="claude-code", target_repo=tmp_target, force=True)
    assert install_starter("full", ctx)
    rules_dir = tmp_target / ".claude" / "rules"
    assert (rules_dir / "multi-repo-safety.md").is_file()
    assert (rules_dir / "persona-integration.md").is_file()
    # Personas
    personas_dir = tmp_target / ".claude" / "personas"
    assert personas_dir.is_dir()
    persona_files = list(personas_dir.glob("*.md"))
    assert len(persona_files) >= 1


# --- Personas ---


def test_install_personas(tmp_target: Path):
    """Personas install copies persona files and config."""
    ctx = InstallContext(tool="claude-code", target_repo=tmp_target, force=True, quiet=True)
    assert install_personas(ctx)
    personas_dir = tmp_target / ".claude" / "personas"
    assert personas_dir.is_dir()
    config = tmp_target / ".claude" / "persona.yaml"
    assert config.is_file()


# --- Install all ---


def test_install_all_dry_run(tmp_target: Path):
    """--all with --dry-run produces no file changes."""
    ctx = InstallContext(tool="claude-code", target_repo=tmp_target, dry_run=True, quiet=True)
    install_all(ctx)
    # No files should be created
    claude_dir = tmp_target / ".claude"
    if claude_dir.exists():
        files = list(claude_dir.rglob("*"))
        assert len(files) == 0


def test_install_all_force(tmp_target: Path):
    """--all --force installs all workflows."""
    ctx = InstallContext(tool="claude-code", target_repo=tmp_target, force=True, quiet=True)
    assert install_all(ctx)
    # Should have rules, skills, agents, and personas
    assert (tmp_target / ".claude" / "rules").is_dir()
    assert (tmp_target / ".claude" / "skills").is_dir()
    assert (tmp_target / ".claude" / "personas").is_dir()


# --- Diff utility ---


def test_files_are_identical():
    assert files_are_identical("hello\n", "hello\n")
    assert files_are_identical("hello\n", "hello")  # Trailing whitespace ignored
    assert not files_are_identical("hello\n", "world\n")
