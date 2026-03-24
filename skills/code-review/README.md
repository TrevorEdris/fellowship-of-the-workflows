# code-review

Thorough code review using the Pragmatic Quality framework with optional Jira integration.

## Usage

```
/code-review                        # Review current pending changes
/code-review --jira PROJ-123        # Review with Jira ticket validation
```

## When to Use

- Before merging a pull request
- After completing a feature implementation
- Validating that changes match ticket acceptance criteria
- Reviewing someone else's PR for quality

## What It Does

- Analyzes PR diffs, commit history, and file changes using Pragmatic Quality framework
- Integrates with Jira to validate implementation against acceptance criteria
- Produces prioritized findings (substantive issues first, style second)

## References

- `references/REVIEW_CHECKLIST.md` — Review criteria and quality framework
