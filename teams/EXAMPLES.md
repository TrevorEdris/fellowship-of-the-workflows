# Agent Teams Examples

Practical scenarios for each team preset and multi-team sequences. All examples use a fictional Express API (`acme-api`) with auth middleware, PostgreSQL, and a React frontend.

---

## Review Team

### Review a PR

```
/team review PR#87
```

Three reviewers analyze the PR in parallel. The security reviewer flags an unvalidated redirect in the OAuth callback. The code-quality reviewer notes the new middleware isn't covered by integration tests. The adversarial reviewer finds a race condition when two sessions refresh tokens simultaneously. The lead synthesizes a unified review with 1 critical, 2 high findings.

### Review uncommitted changes before pushing

```
/team review "the changes on this branch compared to main"
```

Useful when you've been working for a while and want a sanity check before opening a PR. The team reviews your diff the same way they'd review a PR.

### Pre-release audit of a module

```
/team review "src/billing/ — we're launching billing next week, review the entire module"
```

The security reviewer focuses on payment data handling and PCI compliance. The adversarial reviewer stress-tests error paths around failed charges and webhook retries. The code-quality reviewer checks that the module is structured for the team that will maintain it post-launch.

---

## Implementation Team

### Greenfield feature with TDD

```
/team implementation "add a /api/v2/teams endpoint with CRUD operations, scoped to the authenticated user's organization"
```

The test-writer creates failing tests for each CRUD operation and authorization edge case. The implementer makes them pass with minimal code, then refactors. The docs-writer updates the API reference and adds a migration guide. All three coordinate on file ownership — test-writer owns `tests/`, implementer owns `src/`, docs-writer owns `docs/`.

### Bug fix with regression test

```
/team implementation "fix: expired refresh tokens return 500 instead of 401 — see issue #234"
```

The test-writer writes a regression test that reproduces the 500 error with an expired token. The implementer fixes the token validation to return 401. The docs-writer updates the error code reference to document the corrected behavior.

### API migration

```
/team implementation "migrate /api/v1/users to /api/v2/users with the new response schema, keeping v1 working during the transition"
```

The test-writer writes tests for both v1 (unchanged behavior) and v2 (new schema). The implementer builds v2 alongside v1 with shared business logic. The docs-writer documents the migration path and deprecation timeline for v1 consumers.

---

## Investigation Team

### Intermittent production bug

```
/team investigation "users report random 503 errors on /api/auth/refresh — only happens during peak hours, can't reproduce locally"
```

The lead assigns three hypotheses: (A) connection pool exhaustion under load, (B) a race condition in the token refresh logic, (C) an upstream dependency timeout. Each debugger investigates their hypothesis, shares evidence, and actively tries to disprove the others. Debuggers A and B converge on a connection pool issue that only manifests when concurrent refresh requests exceed the pool size.

### Performance regression

```
/team investigation "p99 latency on /api/search jumped from 200ms to 1.2s after the last deploy — no obvious code changes in the diff"
```

Hypotheses: (A) a new database index was dropped or changed, (B) a dependency upgrade introduced a slower code path, (C) the search query plan changed due to data volume growth. The team traces through the deploy diff, database migrations, and query plans.

### CI-only failure

```
/team investigation "test_billing_webhook_retry fails in CI but passes locally — started after upgrading to Node 20"
```

Hypotheses: (A) a timing-sensitive test that depends on system clock behavior, (B) a difference in the CI environment's timezone or locale settings, (C) a Node 20 behavior change in how timers or promises resolve. The debuggers each investigate their angle and cross-check findings.

---

## Design Team

### Choosing an architecture

```
/team design "we need to extract the notification system from the monolith into its own service — evaluate sync vs async approaches"
```

The architect proposes an event-driven approach with SQS and a dedicated notification service. The adversary challenges: what happens when the queue backs up? How do you handle exactly-once delivery for SMS? The code-quality reviewer flags that the proposed event schema couples the notification service to internal domain models. They converge on an async approach with an anti-corruption layer.

### Data model design

```
/team design "we're adding multi-tenancy to acme-api — row-level security vs schema-per-tenant vs database-per-tenant"
```

The architect evaluates each approach against the current PostgreSQL setup. The adversary attacks: schema-per-tenant breaks connection pooling at scale, database-per-tenant makes cross-tenant reporting impossible, row-level security is one missing WHERE clause away from a data breach. The code-quality reviewer evaluates migration complexity and ongoing maintenance burden. They converge on row-level security with a middleware enforcement layer.

### Migration strategy

```
/team design "the auth module uses JWTs stored in localStorage — security audit says move to httpOnly cookies, but we have mobile clients that can't use cookies"
```

The architect proposes a dual-token strategy: cookies for web, short-lived opaque tokens for mobile. The adversary challenges the complexity and attack surface of maintaining two auth paths. The code-quality reviewer evaluates whether the existing auth middleware can support both without becoming unmaintainable. They produce a design decision with trade-offs documented.

---

## Plan Review Team

### Stress-test before approval

```
/team plan-review .ai/sessions/2026-03-19_Add-Rate-Limiting/PLAN.md
```

The architecture reviewer confirms the token bucket approach is sound but flags that the plan doesn't address distributed rate limiting across multiple API instances. The risk analyst finds that step 4 (deploy to staging) has no rollback strategy if rate limiting blocks legitimate traffic. The scope auditor discovers that `src/middleware/cors.ts` is affected by the middleware chain change but isn't listed in the plan. Lead recommends REVISE with 3 specific items.

### Validate after discovery revealed complexity

```
/team plan-review .ai/sessions/2026-03-20_Billing-Migration/PLAN.md
```

Discovery found that the billing module has undocumented dependencies on the legacy user service. The scope auditor confirms the plan accounts for these, but the risk analyst flags that the migration steps don't handle in-flight transactions during the cutover. The architecture reviewer questions whether the phasing is right — phase 2 depends on phase 1 but could actually run in parallel with a feature flag.

### Review a plan from another session

```
/team plan-review ~/src/other-project/.ai/sessions/2026-03-18_Auth-Refactor/PLAN.md
```

Useful when picking up someone else's planned work or reviewing your own plan from a previous session with fresh eyes. The team evaluates the plan against the current codebase state — things may have changed since the plan was written.

---

## Multi-Team Sequences

### Full planning pipeline: design through implementation

A rate limiting feature from idea to code:

```
# 1. Debate the approach (after discovery)
/team design "add rate limiting to the public API — token bucket vs sliding window, per-user vs per-IP"

# 2. Write PLAN.md based on the design decision
#    (done by you or the main session, not a team)

# 3. Stress-test the plan before committing to it
/team plan-review .ai/sessions/2026-03-19_Rate-Limiting/PLAN.md

# 4. Execute the plan
/team implementation "implement rate limiting per the approved plan in PLAN.md"
```

Each team hands off to the next. The design team's output informs the plan. The plan review team's feedback revises the plan. The implementation team executes the final version.

### Review surfaces a bug, investigation finds root cause

```
# 1. Review the PR
/team review PR#92

# Review team finds: "The retry logic in src/billing/webhooks.ts silently
# swallows errors after 3 attempts — this could cause missed payment events"

# 2. Investigate the scope of the problem
/team investigation "how many webhook events are being silently dropped by the retry swallowing in src/billing/webhooks.ts? Is this the cause of the missing invoice reports?"
```

The review team identifies a suspicious pattern. Rather than guessing at the fix, the investigation team determines the actual impact and root cause before anyone writes code.

### Plan review catches scope gap, design resolves it

```
# 1. Plan review flags a problem
/team plan-review .ai/sessions/2026-03-20_Auth-Refactor/PLAN.md

# Plan review finds: "The plan doesn't account for the mobile client's
# token refresh flow — changing the auth middleware will break mobile"

# 2. Design team debates how to handle both web and mobile
/team design "the auth refactor plan needs to support both web (cookies) and mobile (bearer tokens) — what's the right approach?"

# 3. Revise the plan based on the design decision, then re-review
/team plan-review .ai/sessions/2026-03-20_Auth-Refactor/PLAN.md
```

The plan review team surfaces a blind spot. The design team resolves it. The revised plan goes through plan review again for a clean pass.
