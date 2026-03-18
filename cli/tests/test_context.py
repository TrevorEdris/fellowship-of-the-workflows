"""Tests for context resolver and budget estimation."""

from pathlib import Path

from fotw.services.context_budget import CHARS_PER_TOKEN, estimate_file, estimate_skill
from fotw.services.context_resolver import VALID_PHASES, resolve_context


class TestResolveContext:
    def _make_skill(self, tmp_path, manifest_yaml=""):
        """Create a minimal skill directory with optional context-manifest."""
        skill_dir = tmp_path / "test-skill"
        skill_dir.mkdir()
        refs_dir = skill_dir / "references"
        refs_dir.mkdir()

        # Create reference files
        (refs_dir / "always-ref.md").write_text("always content")
        (refs_dir / "discover-ref.md").write_text("discover content")
        (refs_dir / "plan-ref.md").write_text("plan content")
        (refs_dir / "implement-ref.md").write_text("implement content")

        # Build SKILL.md
        frontmatter = "---\nname: test-skill\ndescription: test\n"
        if manifest_yaml:
            frontmatter += manifest_yaml
        frontmatter += "---\n\n# Test Skill\n"
        (skill_dir / "SKILL.md").write_text(frontmatter)

        return skill_dir

    def test_no_manifest_returns_all_files(self, tmp_path):
        skill_dir = self._make_skill(tmp_path)
        files = resolve_context(skill_dir)
        # Should return all files (SKILL.md + 4 reference files)
        assert len(files) == 5

    def test_manifest_always_only(self, tmp_path):
        manifest = (
            "context-manifest:\n"
            "  always:\n"
            "    - references/always-ref.md\n"
        )
        skill_dir = self._make_skill(tmp_path, manifest)
        files = resolve_context(skill_dir)
        # SKILL.md + always-ref.md
        assert len(files) == 2
        names = [f.name for f in files]
        assert "SKILL.md" in names
        assert "always-ref.md" in names

    def test_manifest_with_phase(self, tmp_path):
        manifest = (
            "context-manifest:\n"
            "  always:\n"
            "    - references/always-ref.md\n"
            "  discover:\n"
            "    - references/discover-ref.md\n"
            "  plan:\n"
            "    - references/plan-ref.md\n"
        )
        skill_dir = self._make_skill(tmp_path, manifest)
        files = resolve_context(skill_dir, phase="discover")
        names = [f.name for f in files]
        assert "SKILL.md" in names
        assert "always-ref.md" in names
        assert "discover-ref.md" in names
        assert "plan-ref.md" not in names
        assert len(files) == 3

    def test_manifest_phase_none_returns_always_only(self, tmp_path):
        manifest = (
            "context-manifest:\n"
            "  always:\n"
            "    - references/always-ref.md\n"
            "  discover:\n"
            "    - references/discover-ref.md\n"
        )
        skill_dir = self._make_skill(tmp_path, manifest)
        files = resolve_context(skill_dir, phase=None)
        names = [f.name for f in files]
        assert "SKILL.md" in names
        assert "always-ref.md" in names
        assert "discover-ref.md" not in names

    def test_missing_skill_dir_returns_empty(self, tmp_path):
        files = resolve_context(tmp_path / "nonexistent")
        assert files == []

    def test_missing_referenced_file_skipped(self, tmp_path):
        manifest = (
            "context-manifest:\n"
            "  always:\n"
            "    - references/nonexistent.md\n"
        )
        skill_dir = self._make_skill(tmp_path, manifest)
        files = resolve_context(skill_dir)
        # Only SKILL.md (nonexistent file skipped)
        assert len(files) == 1
        assert files[0].name == "SKILL.md"

    def test_valid_phases(self):
        assert VALID_PHASES == {"discover", "plan", "implement"}


class TestEstimateFile:
    def test_estimates_tokens(self, tmp_path):
        f = tmp_path / "test.md"
        f.write_text("a" * 400)  # 400 chars = 100 tokens
        budget = estimate_file(f)
        assert budget.chars == 400
        assert budget.estimated_tokens == 100

    def test_missing_file_returns_zero(self, tmp_path):
        budget = estimate_file(tmp_path / "missing.md")
        assert budget.chars == 0
        assert budget.estimated_tokens == 0


class TestEstimateSkill:
    def test_estimates_skill(self, tmp_path):
        skill_dir = tmp_path / "test-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("x" * 800)
        refs = skill_dir / "references"
        refs.mkdir()
        (refs / "guide.md").write_text("y" * 400)

        budget = estimate_skill(skill_dir)
        assert budget.name == "test-skill"
        assert budget.file_count == 2
        assert budget.total_chars == 1200
        assert budget.total_tokens == 300

    def test_skips_binary_and_test_files(self, tmp_path):
        skill_dir = tmp_path / "test-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("content")
        (skill_dir / "icon.png").write_bytes(b"\x89PNG")
        tests_dir = skill_dir / "tests"
        tests_dir.mkdir()
        (tests_dir / "golden.jsonl").write_text("test data")

        budget = estimate_skill(skill_dir)
        assert budget.file_count == 1  # Only SKILL.md
