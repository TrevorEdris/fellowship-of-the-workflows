# Discovery Prompts

Work through these questions during the Discover phase. Skip any already answered by the Jira ticket or user context. Record answers in DISCOVERY.md under matching headings.

---

## Problem Space

- What symptom or request triggered this work?
- What is the business impact if nothing changes?
- Who or what is affected? (users, services, data pipelines)

## Current State

- What code paths are involved? (entry points, controllers, services, data layer)
- What tests cover this area? What is untested?
- What is the data model? (tables, columns, relationships)
- What cross-repo or cross-service dependencies exist?

## Constraints

- What cannot change? (API contracts, DB schema, external integrations)
- What org policies apply? (no FKs, TDD, branch protection, deployment sequence)
- What has been tried before? (prior PRs, reverted changes, known dead ends)

## Target State

- What does "done" look like in concrete terms?
- What behavior should change? What must NOT change?
- What are the edge cases and failure modes?
