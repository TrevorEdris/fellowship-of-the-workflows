# Code Review Checklist (Hierarchical)

Apply in priority order. Critical issues block merge.

## 1. Architectural Design & Integrity (Critical)

- [ ] Design aligns with existing architectural patterns
- [ ] Appropriately modular (Single Responsibility Principle)
- [ ] No unnecessary complexity — simpler solution possible?
- [ ] Atomic change (single purpose, not bundling unrelated changes)
- [ ] Appropriate abstraction levels and separation of concerns

## 2. Functionality & Correctness (Critical)

- [ ] Correctly implements intended business logic
- [ ] Edge cases handled (null, empty, boundary values)
- [ ] Error conditions handled gracefully
- [ ] No race conditions or concurrency issues
- [ ] State management and data flow correct
- [ ] Idempotent where appropriate

## 3. Security (Non-Negotiable)

- [ ] All user input validated, sanitized, escaped
- [ ] No SQL injection vectors
- [ ] No command injection in subprocess calls
- [ ] No XSS vulnerabilities
- [ ] Auth/authz checks on all protected resources
- [ ] No hardcoded secrets, API keys, credentials
- [ ] No sensitive data in logs or error messages
- [ ] CORS/CSP headers appropriate (if applicable)

## 4. Maintainability & Readability (High Priority)

- [ ] Code clear for future developers
- [ ] Variable/function/class names descriptive and consistent
- [ ] Control flow complexity reasonable (nesting depth ≤3)
- [ ] Comments explain "why" (intent/trade-offs) not "what"
- [ ] Error messages aid debugging
- [ ] No code duplication that should be refactored

## 5. Testing Strategy (High Priority)

- [ ] Test coverage sufficient for complexity/criticality
- [ ] Happy path tested
- [ ] Failure modes and error paths tested
- [ ] Edge cases tested
- [ ] Test code clean, maintainable, efficient
- [ ] Appropriate test isolation and mock usage
- [ ] Integration tests for critical paths

## 6. Performance & Scalability (Important)

- [ ] No N+1 query patterns
- [ ] Appropriate indexes for new queries
- [ ] Efficient algorithms (no unnecessary O(n²))
- [ ] Caching strategy appropriate
- [ ] Pagination for large datasets
- [ ] No memory leaks or resource exhaustion
- [ ] Bundle size impact acceptable (frontend)

## 7. Dependencies & Documentation (Important)

- [ ] New dependencies necessary and vetted
- [ ] Dependency security and maintenance status reviewed
- [ ] License compatibility verified
- [ ] API documentation updated for contract changes
- [ ] README updated if needed

## 8. Boot-Time Wiring & Configuration Completeness (Critical)

- [ ] For any changed config flag that gates a code path (e.g. `feature.enabled: true`), trace it to the component it activates and confirm every config block that component's DI provider dereferences is present in that environment's config file
- [ ] Configuration diffed across ALL environments (dev / staging / prod and any regional variants) — a key present in one environment and absent in another is a finding unless intentional
- [ ] For DI-provisioned services, identified which beans are eagerly provisioned at startup (registered with the app lifecycle in run/bootstrap); their full transitive provider chain executes at boot, so a null or thrown exception there crashes the deploy, not a single request
- [ ] Config-backed factory fields that are nullable (no non-null validation, no default) but dereferenced by an eagerly-provisioned provider (e.g. `config.getX().build()`) are flagged — a missing config block means `getX()` returns null and an NPE at boot; verify a non-null validation annotation OR a safe default
- [ ] "Compiles and unit tests pass" treated as insufficient for boot-crash risk — these defects are environment-specific and only surface on deploy

## Ticket Alignment (when Jira available)

- [ ] Implementation matches ticket title/summary
- [ ] All acceptance criteria addressed
- [ ] No undocumented scope additions
- [ ] Edge cases from ticket discussion handled
