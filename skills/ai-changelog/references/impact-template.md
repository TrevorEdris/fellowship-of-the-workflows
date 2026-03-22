# Impact Assessment Template

Use this template for each significant finding.

```markdown
## Impact Assessment

### New Feature: [feature name]
- **Tool:** [which AI coding tool]
- **Date:** [when announced/released]
- **Release stage:** [stable | experimental | beta/preview]
- **What changed:** [1-2 sentences]
- **Project impact:**
  - [ ] New workflow needed? (skill, rule, agent, hook)
  - [ ] Existing workflow update? Which: ___
  - [ ] Configuration change needed?
  - [ ] No action needed
- **Recommendation:** [specific action or "monitor"]
- **Priority:** [high/medium/low]
- **Affected files:** [list specific workflow files]
```

## Priority Guidelines

- **High:** Feature directly obsoletes or breaks an existing workflow, or enables a capability the project needs
- **Medium:** Feature improves a workflow that already exists, or opens new possibilities worth exploring
- **Low:** Informational only, no immediate project impact

### Release Stage Modifier

Experimental features with high project relevance default to **medium** until GA, unless the user explicitly opts into experimental channels. Beta/preview features follow the same rule.
