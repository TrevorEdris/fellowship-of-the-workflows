---
name: test-driven-development
description: "Enforce RED-GREEN-REFACTOR cycle for any implementation task. Write failing test first, implement minimally, refactor. Triggered by: write tests first, do TDD, red-green-refactor, test-first approach, I want to follow TDD, test-driven. Use when implementing features, fixing bugs, or refactoring code."
agent: tdd-enforcer
allowed-tools: Bash(npm:*), Bash(npx:*), Bash(pytest:*), Bash(go:*), Bash(cargo:*), Bash(make:*), Bash(task:*), Grep, Glob, Read
tags: [testing]
tier: core
---

# Test-Driven Development

Write the test first. Watch it fail. Write minimal code to pass.

---

## Context

Current repository state:
```
!`git status`
```

Project manifest:
```
!`cat package.json 2>/dev/null || cat pyproject.toml 2>/dev/null || cat go.mod 2>/dev/null || cat Cargo.toml 2>/dev/null || echo "No project manifest found"`
```

Task runner:
```
!`ls **/Makefile **/Taskfile.yml 2>/dev/null || echo "No task runner found"`
```

---

## Test Runner Discovery

Before writing a single line of code, identify how to run tests in this project.

| Project File | Test Command |
|---|---|
| `package.json` | `npm test` or check `scripts.test` |
| `pyproject.toml` | `pytest` |
| `go.mod` | `go test ./...` |
| `Cargo.toml` | `cargo test` |
| `Makefile` | `make test` |
| `Taskfile.yml` | `task test` |

If none of these apply, or the command is unclear: **ask the user before proceeding.**

---

## The Iron Law

**NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST.**

This is not a workflow preference. It is a hard constraint. Every function, method, handler, and helper must be preceded by a test that fails because the implementation does not yet exist.

If you wrote production code before writing a test:
- **Delete it.** Not "adapt it." Not "keep it as a reference." Delete it.
- Write the test first.
- Implement again from scratch.

---

## The RED-GREEN-REFACTOR Cycle

### RED: Write a Failing Test

Write a test that captures exactly one behavior. Guidelines:
- **One behavior per test.** Do not test multiple things in one test case.
- **Descriptive test name.** The name should explain what behavior is expected: `test_empty_email_returns_validation_error`, not `test_validate`.
- **Use real code.** Avoid mocks unless the dependency is an external service with network I/O. Test behavior through real code paths.
- **Show the desired API.** The test defines the interface—write the test as if the production code already exists.

### Verify RED (MANDATORY)

Run the test command. Observe the output.

- Confirm the test **fails** — not errors, **fails**.
- Confirm the failure message **matches the expected missing behavior**. If the test fails with a syntax error or import error, fix that first — it is not a valid RED.
- If the test passes without any implementation: you are testing existing behavior. Revise the test to capture the new, missing behavior.

**Do not proceed to GREEN until RED is confirmed.**

### GREEN: Minimal Implementation

Write the simplest code that makes the test pass.

- **Do not add features.** If the test does not require it, do not write it.
- **Do not refactor yet.** Ugly code that passes is correct at this stage.
- **Do not improve beyond test requirements.** Premature generalization is a violation.

Hardcoding a return value to pass a single test is acceptable. The next test will force real logic.

### Verify GREEN (MANDATORY)

Run the full test suite. Observe the output.

- Confirm the new test **passes**.
- Confirm **all other tests still pass**. A passing new test that breaks existing tests is not GREEN.
- Confirm **no warnings or errors** appear in the output.

If the new test fails: fix the production code, not the test.
If existing tests fail: fix the regression before moving forward.

**Do not proceed to REFACTOR until GREEN is confirmed across the full suite.**

### REFACTOR: Clean Up

Only after GREEN, clean the implementation:

- Remove duplication.
- Improve variable and function names.
- Extract helpers or utilities.
- Improve readability.

**Do not add new behavior during REFACTOR.** Any new behavior requires a new RED test.

### Verify REFACTOR (MANDATORY)

Run the full test suite. All tests must be green. No warnings.

If any test fails: the refactor introduced a regression. Revert or fix before proceeding.

### REPEAT

Move to the next behavior. Write the next failing test. Continue the cycle.

---

## Common Rationalizations

| Excuse | Reality |
|---|---|
| "It's too simple to need a test." | Simple code breaks too. Tests document behavior. Write it. |
| "I'll write the tests after I'm done." | You won't. Retrofitting tests to existing code produces tests that pass by construction, not by verification. |
| "I already manually tested this in the console." | Manual tests do not run on CI. They do not prevent regressions. Write the automated test. |
| "Deleting my code is wasteful — I put effort into it." | Code written without tests is unverified code. Its existence is the problem. Delete it. |
| "I'll keep it as a reference while writing the test." | The reference will influence the test, defeating the purpose. Delete it. |
| "I need to explore first to understand the problem space." | Exploration is valid. Write throwaway spike code. Then delete it and start TDD. |
| "This code is hard to test, so I'll skip TDD for it." | Hard-to-test code is a design signal. Difficult testing usually means poor separation of concerns. TDD will improve the design. |
| "TDD will slow me down." | TDD eliminates time spent debugging, manually verifying, and fixing regressions. It is faster in aggregate. |
| "The test framework isn't set up yet." | Set it up. Running without tests is not faster — it is deferred cost with interest. |
| "This is a refactor, not new behavior." | Refactoring without tests to verify existing behavior is rewriting, not refactoring. Write characterization tests first. |
| "The requirements will change, so tests aren't worth it." | Tests validate requirements. When requirements change, tests tell you what broke. |
| "I'm just fixing a typo / renaming a variable." | Typos and renames can change behavior unexpectedly. Tests catch that. |

---

## Red Flags — STOP and Start Over

If any of these are true, TDD was violated. Delete the production code and restart:

- You wrote implementation code before any test file was modified.
- You cannot run a specific test that fails because the feature does not exist yet.
- All your tests were written after the implementation was complete.
- You are testing that your implementation returns what it returns, not that it behaves correctly.
- Your tests mock so extensively that no real code paths are exercised.
- You ran the test suite once, at the end, to confirm everything passes.

---

## Bug Fix Protocol

Bugs must be fixed with TDD. The test is the reproduction case.

1. **Reproduce the bug as a failing test.** Write a test that demonstrates the incorrect behavior. Run it. Confirm it fails.
2. **Verify RED.** The failure must show the bug, not an unrelated error.
3. **Fix the bug minimally.** Change only what is needed to make the test pass.
4. **Verify GREEN.** New test passes. All existing tests pass. No warnings.
5. **Refactor if needed.** Clean up. Verify again.

Example (TypeScript):
```typescript
// RED: test reveals the bug
it('should reject empty email addresses', () => {
  expect(validateEmail('')).toBe(false);
});
// Run: FAIL — validateEmail('') returns true

// GREEN: minimal fix
function validateEmail(email: string): boolean {
  if (email.trim() === '') return false;
  return EMAIL_REGEX.test(email);
}
// Run: PASS
```

---

## Integration with Discover-Plan-Implement

TDD is not separate from the workflow — it is embedded in the implementation phase.

- **During Plan phase:** The PLAN.md must include a test strategy section. Specify: what behaviors will be tested, what test files will be created or modified, and whether existing coverage tooling will be used.
- **During Implement phase:** Every implementation step follows the RED-GREEN-REFACTOR cycle. Steps in the plan should be decomposed to the granularity of individual test cases.
- **Post-implementation:** Run the full test suite. If coverage tooling is available, run it and report the delta. Suggest `/code-review` before committing.

---

## Coverage Verification (Optional)

If the project has coverage tooling configured, run it after completing all TDD cycles.

| Tool | Command |
|---|---|
| Jest (JS/TS) | `npm test -- --coverage` |
| pytest | `pytest --cov` |
| Go | `go test -cover ./...` |
| Rust | `cargo tarpaulin` |

Report the coverage delta (before and after, if measurable). Coverage is not a hard gate — a poorly written test can achieve 100% coverage while validating nothing. Use it as a signal, not a target.

---

## Verification Checklist

Before marking implementation complete, confirm all items:

- [ ] Every new function and method has at least one test
- [ ] Each test was written before its corresponding implementation
- [ ] Each test was observed to fail (RED) before implementing
- [ ] Each failure was for the expected reason — missing behavior, not a test error
- [ ] Minimal implementation was written to pass each test
- [ ] All tests pass after implementation
- [ ] No warnings or errors appear in the test output
- [ ] Tests exercise real code paths (mocks used only for external I/O)
- [ ] Edge cases are covered (empty inputs, boundary values, error paths)
- [ ] The full test suite passes, not just the new tests

See `assets/verification-checklist.md` for a standalone copy to fill in per implementation task.

---

## When Stuck

| Problem | Solution |
|---|---|
| Cannot determine how to test this code | Examine the dependencies. The difficulty usually indicates a design problem. Extract the logic from its dependencies and test the pure logic. |
| Test requires massive setup | The code under test does too much. Break it into smaller units and test each. |
| Cannot observe a meaningful failure (test passes immediately) | The test is not targeting missing behavior. Revise to assert something that cannot be true without implementation. |
| Existing tests break when writing new ones | Run the full suite before and after each change. Isolate the conflict. Fix the regression before continuing. |
| Unsure what behavior to test next | List all behaviors the feature requires. Pick the simplest unimplemented one. Write a test for it. |
| Test runner command is unclear | Ask the user. Do not guess. |
| Mock depth keeps growing | Stop. You are testing mocks. Extract the logic being tested, make it a pure function, test that instead. |

---

## References

- `references/testing-anti-patterns.md` — Iron laws, anti-pattern catalog, and gate functions for common testing mistakes
- `references/tdd-cycle-examples.md` — Concrete RED-GREEN-REFACTOR examples in TypeScript, Python, and Go
- `assets/verification-checklist.md` — Standalone checklist template for each implementation task
