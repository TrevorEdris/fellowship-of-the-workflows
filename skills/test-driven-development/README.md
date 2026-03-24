# test-driven-development

Enforces the RED-GREEN-REFACTOR cycle for any implementation task.

## Usage

```
/tdd                                # Start TDD cycle for current task
```

## When to Use

- Implementing a new feature and want to write tests first
- Fixing a bug and want to reproduce it as a failing test before patching
- Refactoring code where behavior changes need test coverage
- Teaching yourself or a team the TDD discipline

## What It Does

- Guides the RED-GREEN-REFACTOR cycle with test runner auto-discovery
- Enforces failing test before any production code is written
- Discovers the correct test command for your stack (npm, pytest, go, cargo, make, task)

## References

- `references/tdd-cycle-examples.md` — Worked examples per language
- `references/testing-anti-patterns.md` — Common TDD mistakes to avoid
