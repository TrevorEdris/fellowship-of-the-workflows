"""Tests for eval runner — deterministic assertions only."""

import json

import pytest

from fotw.services.eval_runner import (
    Assertion,
    TestCase,
    check_assertion,
    load_golden_tests,
    run_test_deterministic,
)


class TestCheckAssertion:
    def test_contains_pass(self):
        result = check_assertion(Assertion("contains", "SQL injection"), "Found SQL injection risk")
        assert result.passed is True

    def test_contains_fail(self):
        result = check_assertion(Assertion("contains", "SQL injection"), "Code looks clean")
        assert result.passed is False

    def test_contains_case_insensitive(self):
        result = check_assertion(Assertion("contains", "sql injection"), "Found SQL INJECTION risk")
        assert result.passed is True

    def test_not_contains_pass(self):
        result = check_assertion(Assertion("not-contains", "looks good"), "Found critical vulnerability")
        assert result.passed is True

    def test_not_contains_fail(self):
        result = check_assertion(Assertion("not-contains", "looks good"), "The code looks good overall")
        assert result.passed is False

    def test_regex_pass(self):
        result = check_assertion(Assertion("regex", r"parameteriz|prepared"), "Use parameterized queries")
        assert result.passed is True

    def test_regex_fail(self):
        result = check_assertion(Assertion("regex", r"parameteriz|prepared"), "The code is fine")
        assert result.passed is False

    def test_regex_case_insensitive(self):
        result = check_assertion(Assertion("regex", r"SQL"), "potential sql issue")
        assert result.passed is True

    def test_llm_rubric_deferred(self):
        result = check_assertion(Assertion("llm-rubric", "Should flag injection"), "any output")
        assert result.passed is None
        assert "LLM judge" in result.reason

    def test_unknown_type(self):
        result = check_assertion(Assertion("unknown", "value"), "output")
        assert result.passed is None


class TestRunTestDeterministic:
    def test_all_pass(self):
        case = TestCase(
            id="t-001", name="test", input="input",
            assertions=[
                Assertion("contains", "vulnerability"),
                Assertion("not-contains", "looks good"),
            ],
        )
        result = run_test_deterministic(case, "Found a vulnerability in the code")
        assert result.passed is True

    def test_one_fails(self):
        case = TestCase(
            id="t-002", name="test", input="input",
            assertions=[
                Assertion("contains", "vulnerability"),
                Assertion("contains", "missing keyword"),
            ],
        )
        result = run_test_deterministic(case, "Found a vulnerability")
        assert result.passed is False

    def test_deferred_means_not_passed(self):
        case = TestCase(
            id="t-003", name="test", input="input",
            assertions=[
                Assertion("contains", "found"),
                Assertion("llm-rubric", "Should be helpful"),
            ],
        )
        result = run_test_deterministic(case, "found it")
        assert result.passed is False  # deferred = not yet passed


class TestLoadGoldenTests:
    def test_load_valid_jsonl(self, tmp_path):
        skill_dir = tmp_path / "test-skill"
        tests_dir = skill_dir / "tests"
        tests_dir.mkdir(parents=True)
        golden = tests_dir / "golden.jsonl"
        golden.write_text(json.dumps({
            "id": "t-001",
            "name": "test-case",
            "input": "test input",
            "assertions": [{"type": "contains", "value": "expected"}],
            "tags": ["regression"],
        }) + "\n")
        cases = load_golden_tests(skill_dir)
        assert len(cases) == 1
        assert cases[0].id == "t-001"
        assert len(cases[0].assertions) == 1

    def test_tag_filter(self, tmp_path):
        skill_dir = tmp_path / "test-skill"
        tests_dir = skill_dir / "tests"
        tests_dir.mkdir(parents=True)
        golden = tests_dir / "golden.jsonl"
        lines = [
            json.dumps({"id": "t-001", "name": "a", "input": "x", "assertions": [], "tags": ["security"]}),
            json.dumps({"id": "t-002", "name": "b", "input": "y", "assertions": [], "tags": ["regression"]}),
        ]
        golden.write_text("\n".join(lines) + "\n")
        cases = load_golden_tests(skill_dir, tag_filter="security")
        assert len(cases) == 1
        assert cases[0].id == "t-001"

    def test_missing_file_returns_empty(self, tmp_path):
        cases = load_golden_tests(tmp_path / "nonexistent")
        assert cases == []

    def test_invalid_json_raises(self, tmp_path):
        skill_dir = tmp_path / "test-skill"
        tests_dir = skill_dir / "tests"
        tests_dir.mkdir(parents=True)
        golden = tests_dir / "golden.jsonl"
        golden.write_text("not valid json\n")
        with pytest.raises(ValueError, match="Invalid JSON"):
            load_golden_tests(skill_dir)
