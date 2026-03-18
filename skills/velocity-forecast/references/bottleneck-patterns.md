# Sprint Bottleneck Patterns

Common patterns that slow team velocity, with detection signals and mitigations.

## 1. Review Bottleneck

**Signal:** PR age >3 days, few reviewers active, PRs pile up in "awaiting review."

**Root Cause:** Too few people with review capacity or context to review effectively.

**Mitigations:**
- Assign rotating reviewer duty (each person reviews N PRs per day)
- Break large PRs into smaller, reviewable chunks (<400 lines)
- Use CODEOWNERS to auto-assign reviewers
- Set team SLA: reviews started within 4 business hours

## 2. CI Bottleneck

**Signal:** PRs sit in "checks pending" for >10 minutes. Developers context-switch while waiting.

**Root Cause:** Slow CI pipeline — sequential tests, no caching, large Docker images.

**Mitigations:**
- Parallelize test suites
- Cache dependencies (npm, pip, Docker layers)
- Use test impact analysis to run only affected tests
- Split pipeline: fast lint/type-check gate + slower full suite

## 3. Scope Creep

**Signal:** PRs grow >500 lines. Review comments increase. Merge conflicts rise.

**Root Cause:** Features not broken into atomic, independently shippable increments.

**Mitigations:**
- Enforce <400 lines per PR as a team norm
- Use feature flags for incremental delivery
- Plan work in vertical slices (UI + API + DB per slice)
- "If it needs a 2-paragraph description, it's too big"

## 4. Knowledge Silos

**Signal:** Bus factor <2 for a subsystem. One person always assigned certain PRs.

**Root Cause:** Expertise concentrated in one person. Others don't touch the subsystem.

**Mitigations:**
- Pair programming on unfamiliar areas
- Rotate on-call and incident response across the team
- Write architecture decision records (ADRs) for critical subsystems
- Require at least 2 people to have committed to each directory in the last 90 days

## 5. Dependency Blocking

**Signal:** Work items sitting in "blocked" status. PRs waiting on upstream changes.

**Root Cause:** Cross-team or cross-repo dependencies without interface contracts.

**Mitigations:**
- Define API contracts (OpenAPI, protobuf) before implementation starts
- Use mocks and stubs to unblock parallel development
- Establish cross-team integration windows
- Prefer eventual consistency patterns over synchronous dependencies

## 6. Tech Debt Snowball

**Signal:** Debt density increasing sprint-over-sprint. Velocity declining despite stable headcount.

**Root Cause:** Shortcuts accumulate faster than they're resolved. Each shortcut adds friction to future work.

**Mitigations:**
- Allocate 20% of each sprint to debt reduction (not negotiable)
- Track debt markers in CI — fail builds if debt grows beyond threshold
- Prioritize debt by blast radius: fix the ones blocking the most people first
- "If you touch a file, leave it cleaner than you found it" (Boy Scout Rule)
