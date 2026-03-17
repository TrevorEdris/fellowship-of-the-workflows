"""Eval runner for skill golden tests."""

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal


@dataclass(frozen=True)
class Assertion:
    """A single assertion to check against skill output."""
    type: Literal["contains", "not-contains", "regex", "llm-rubric", "json-schema"]
    value: str


@dataclass
class TestCase:
    """A single golden test case."""
    id: str
    name: str
    input: str
    assertions: list[Assertion]
    description: str = ""
    tags: list[str] = field(default_factory=list)
    config: dict = field(default_factory=dict)


@dataclass
class AssertionResult:
    """Result of checking one assertion."""
    type: str
    value: str
    passed: bool | None      # None = deferred (requires LLM judge)
    reason: str = ""


@dataclass
class TestResult:
    """Result of running one test case."""
    case_id: str
    case_name: str
    passed: bool
    assertions: list[AssertionResult] = field(default_factory=list)
    output: str = ""          # The actual skill output (for debugging)
    error: str | None = None  # If the test itself failed to run


@dataclass
class EvalReport:
    """Aggregate results for an eval run."""
    skill_name: str
    total: int
    passed: int
    failed: int
    deferred: int             # Tests with unresolved llm-rubric assertions
    results: list[TestResult] = field(default_factory=list)

    @property
    def score(self) -> str:
        return f"{self.passed}/{self.total}"


def load_golden_tests(skill_dir: Path, tag_filter: str | None = None) -> list[TestCase]:
    """Load golden test cases from skills/<name>/tests/golden.jsonl.

    Returns empty list if no golden file exists (not an error — most skills won't have tests yet).
    """
    golden_file = skill_dir / "tests" / "golden.jsonl"
    if not golden_file.is_file():
        return []

    cases = []
    for line_num, line in enumerate(golden_file.read_text().splitlines(), start=1):
        line = line.strip()
        if not line or line.startswith("#"):  # Allow comments
            continue
        try:
            data = json.loads(line)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON at {golden_file}:{line_num}: {e}") from e

        assertions = [Assertion(type=a["type"], value=a["value"]) for a in data.get("assertions", [])]
        case = TestCase(
            id=data["id"],
            name=data["name"],
            input=data["input"],
            assertions=assertions,
            description=data.get("description", ""),
            tags=data.get("tags", []),
            config=data.get("config", {}),
        )
        if tag_filter and tag_filter not in case.tags:
            continue
        cases.append(case)
    return cases


def check_assertion(assertion: Assertion, output: str) -> AssertionResult:
    """Check a single assertion against output. Returns result immediately for
    deterministic types. Returns passed=None for types requiring external evaluation."""
    if assertion.type == "contains":
        passed = assertion.value.lower() in output.lower()
        reason = "" if passed else f"Expected output to contain '{assertion.value}'"
        return AssertionResult(type=assertion.type, value=assertion.value, passed=passed, reason=reason)

    elif assertion.type == "not-contains":
        passed = assertion.value.lower() not in output.lower()
        reason = "" if passed else f"Expected output NOT to contain '{assertion.value}'"
        return AssertionResult(type=assertion.type, value=assertion.value, passed=passed, reason=reason)

    elif assertion.type == "regex":
        passed = bool(re.search(assertion.value, output, re.IGNORECASE | re.DOTALL))
        reason = "" if passed else f"Pattern '{assertion.value}' not found in output"
        return AssertionResult(type=assertion.type, value=assertion.value, passed=passed, reason=reason)

    elif assertion.type == "llm-rubric":
        # Deferred — requires LLM judge call via eval_provider
        return AssertionResult(
            type=assertion.type,
            value=assertion.value,
            passed=None,
            reason="Requires LLM judge — run with --provider to evaluate",
        )

    elif assertion.type == "json-schema":
        try:
            import jsonschema
            schema = json.loads(assertion.value) if isinstance(assertion.value, str) else assertion.value
            parsed = json.loads(output)
            jsonschema.validate(parsed, schema)
            return AssertionResult(type=assertion.type, value=assertion.value, passed=True)
        except ImportError:
            return AssertionResult(type=assertion.type, value=assertion.value, passed=None,
                                  reason="jsonschema not installed — pip install jsonschema")
        except (json.JSONDecodeError, Exception) as e:
            return AssertionResult(type=assertion.type, value=assertion.value, passed=False, reason=str(e))

    return AssertionResult(type=assertion.type, value=assertion.value, passed=None, reason=f"Unknown type: {assertion.type}")


def run_test_deterministic(case: TestCase, output: str) -> TestResult:
    """Run all deterministic assertions for a test case. LLM-rubric assertions are deferred."""
    assertion_results = []
    all_passed = True
    has_deferred = False

    for assertion in case.assertions:
        result = check_assertion(assertion, output)
        assertion_results.append(result)
        if result.passed is None:
            has_deferred = True
        elif not result.passed:
            all_passed = False

    return TestResult(
        case_id=case.id,
        case_name=case.name,
        passed=all_passed and not has_deferred,
        assertions=assertion_results,
        output=output[:500],  # Truncate for report size
    )


def format_report(report: EvalReport) -> dict:
    """Format eval report as JSON-serializable dict."""
    return {
        "skill": report.skill_name,
        "score": report.score,
        "total": report.total,
        "passed": report.passed,
        "failed": report.failed,
        "deferred": report.deferred,
        "results": [
            {
                "id": r.case_id,
                "name": r.case_name,
                "passed": r.passed,
                "assertions": [
                    {"type": a.type, "value": a.value, "passed": a.passed, "reason": a.reason}
                    for a in r.assertions
                ],
                "error": r.error,
            }
            for r in report.results
        ],
    }
