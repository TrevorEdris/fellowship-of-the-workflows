# Velocity Metrics Guide

## Velocity (PRs merged per week)

Measures the throughput of completed work flowing into the main branch.

| Status | Range | Interpretation |
|--------|-------|---------------|
| Healthy | Stable or slowly increasing | Team is shipping at a sustainable pace |
| Warning | >20% decline for 2 consecutive weeks | Investigate: review bottleneck? scope creep? blocked dependencies? |
| Critical | >20% decline for 3+ consecutive weeks | Systemic issue — review process, team capacity, or technical debt is choking output |

**Caveats:** Raw PR count doesn't capture PR size. A week with 2 large PRs may deliver more value than a week with 10 trivial ones. Use alongside cycle time.

## Cycle Time (PR open to merge)

Measures how long work-in-progress sits before completion.

| Status | Range | Interpretation |
|--------|-------|---------------|
| Healthy | <24h for small PRs (<200 lines) | Fast feedback loop, low context-switching cost |
| Warning | 1-3 days average | Review capacity may be tight |
| Critical | >3 days average | PRs are aging — reviewers are bottlenecked or PRs are too large |

## Debt Density (markers per 1K LOC)

Counts `TODO`, `FIXME`, `HACK`, `XXX`, and `WORKAROUND` comments relative to codebase size.

| Status | Range | Interpretation |
|--------|-------|---------------|
| Healthy | <5 per 1K LOC | Normal levels of acknowledged shortcuts |
| Concerning | 5-10 per 1K LOC | Debt is accumulating — allocate sprint time to reduction |
| Critical | >10 per 1K LOC | Debt is a drag on velocity — dedicated debt sprint needed |

**Trend matters more than absolute count.** A codebase at 8/1K LOC that's been stable for months is better than one at 4/1K LOC that doubled in the last sprint.

## Bus Factor

Number of contributors with >10% of recent commits (last 90 days).

| Status | Range | Interpretation |
|--------|-------|---------------|
| Healthy | 3+ | Knowledge is distributed |
| Risk | 2 | Moderate risk — start cross-training |
| Critical | 1 | Single point of failure — prioritize knowledge sharing |

## PR Age (oldest open PR)

How long the oldest unmerged PR has been open.

| Status | Range | Interpretation |
|--------|-------|---------------|
| Healthy | All PRs <5 days | Work flows steadily |
| Warning | PRs 5-14 days old | Some PRs are stalling |
| Critical | PRs >14 days old | Abandoned or blocked work — close or unblock |
