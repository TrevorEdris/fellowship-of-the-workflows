# refactoring

Systematic code refactoring with smell detection, prioritized planning, and test-verified execution.

## Usage

```
/refactoring                        # Analyze and refactor current code
```

## When to Use

- Code is messy and needs structural cleanup
- Preparing code for a new feature by reducing complexity first
- Paying down tech debt in a specific module
- Extracting methods, removing dead code, or inverting dependencies

## What It Does

- Detects code smells using language-specific analysis tools
- Produces a triaged refactoring plan (Design Discussion / Active Smell / Quick Fix)
- Executes changes one at a time with test verification after each step

## References

- `references/CODE_SMELLS.md` — Smell catalog with detection heuristics
- `references/DETECTION_TOOLS.md` — Language-specific analysis tools
- `references/REFACTORING_TECHNIQUES.md` — Safe transformation patterns
