# Work Review Criteria

Use these criteria when evaluating work accomplished over a time period.

## Epic & Initiative Alignment

- [ ] Work contributes to clear initiatives (linked to epics)
- [ ] Minimal scattered work without epic association
- [ ] Focus on 1-3 major initiatives vs spreading thin
- [ ] Context switching appears manageable

## Completeness

- [ ] All committed tickets show as resolved/closed in Jira
- [ ] No tickets left in "In Progress" for extended periods
- [ ] Scope of work matches sprint/period commitments

## Quality Indicators

### Code Quality
- [ ] Reasonable test coverage added with changes
- [ ] Code review feedback addressed promptly
- [ ] Low rework rate (few fix-up commits after initial implementation)

### Documentation
- [ ] Tech docs created/updated for significant features
- [ ] README updates where applicable
- [ ] Code comments for complex logic

### Process Adherence
- [ ] Commits reference Jira tickets
- [ ] PRs follow template structure
- [ ] Changes went through code review

## Work Distribution

### By Type
- **Features:** New functionality added
- **Bug Fixes:** Issues resolved
- **Tech Debt:** Refactoring, cleanup, upgrades
- **Ops/Infra:** Configuration, deployment, monitoring

### By Complexity
- **Large:** Multi-day efforts, significant changes
- **Medium:** Standard feature/fix work
- **Small:** Quick fixes, minor updates

## Collaboration

- [ ] Participated in code reviews (as reviewer)
- [ ] Cross-team contributions if applicable
- [ ] Knowledge sharing (docs, pairing, etc.)

## PR Review Patterns

### Healthy Patterns
- Most PRs merge within 1-2 review rounds
- Review feedback is varied (not same issues repeatedly)
- Reasonable time from PR open to merge
- Diverse set of reviewers

### Patterns to Discuss
- **Frequent multi-round reviews:** May indicate rushing to PR, unclear requirements, or knowledge gaps
- **Recurring feedback themes:** Suggests specific area for improvement
- **Long review times:** May indicate PR size, availability, or complexity issues
- **Single reviewer dependency:** Risk if that person is unavailable

### Common Feedback Categories
When analyzing PR comments, look for patterns in:
- **Code style/formatting:** Linting, naming conventions
- **Architecture/design:** Structure, abstractions, patterns
- **Testing:** Missing tests, test quality, coverage
- **Edge cases:** Error handling, null checks, boundaries
- **Performance:** Efficiency concerns, N+1, caching
- **Documentation:** Comments, README updates, API docs

## Observations to Note

### Positive Patterns
- Consistent commit frequency
- High-quality commit messages
- Good ticket hygiene
- Proactive tech debt work

### Areas for Discussion
- Extended periods without commits
- High ratio of commits without tickets
- Frequent rework patterns
- Scope changes mid-sprint

## Questions for Review Discussion

1. What were the biggest accomplishments this period?
2. What challenges were encountered?
3. What would you do differently?
4. What support or resources would help?
5. What are the goals for the next period?

### If Multi-Round PR Pattern Detected
6. What factors contributed to PRs needing multiple review rounds?
7. Would earlier design discussions or pairing help?
8. Are there knowledge areas where additional training would help?

### If Scattered Work Pattern Detected
9. Was the context switching intentional or reactive?
10. How can work be better focused on key initiatives?

## Generating Actionable Feedback

When creating recommendations, ensure they are:
- **Specific:** Not "improve code quality" but "consider adding unit tests before PR, based on 5 PRs with test coverage feedback"
- **Actionable:** Something the person can actually do
- **Balanced:** Include what's going well, not just improvements
- **Forward-looking:** Focus on future improvement, not blame

### Example Recommendations

**Process Improvement:**
- "Consider running linter locally before pushing — 4 PRs had formatting feedback"
- "Smaller PRs may reduce review cycles — 3 large PRs had 4+ rounds each"

**Skill Development:**
- "Edge case handling was common feedback — consider defensive programming patterns"
- "SQL performance came up twice — database query optimization may be valuable"

**Collaboration:**
- "Expand reviewer pool — 80% of reviews from same 2 people"
- "Consider design review before implementation for complex features"
