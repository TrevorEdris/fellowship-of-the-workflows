# Blameless Postmortem Template

Use this template after every SEV0 (always) and SEV1 (always). SEV2 postmortems are optional but recommended if the same root cause has occurred 3+ times.

**Blameless principle:** This document exists to improve systems, not assign blame. People make reasonable decisions given the information they had at the time. Focus on system conditions and contributing factors, not individual mistakes.

---

## Template

```markdown
# Postmortem: [Incident Title]

**Date of Incident:** YYYY-MM-DD
**Severity:** SEV[0/1]
**Duration:** [HH:MM from detection to resolution]
**Author(s):** [names or handles]
**Postmortem Meeting Date:** YYYY-MM-DD
**Status:** Draft | In Review | Approved

---

## Impact Summary

| Field | Value |
|---|---|
| Start Time | YYYY-MM-DD HH:MM TZ |
| Detection Time | YYYY-MM-DD HH:MM TZ |
| Resolution Time | YYYY-MM-DD HH:MM TZ |
| Total Duration | HH:MM |
| Detection Lag | HH:MM (from start to detection) |
| Users Affected | [count or percentage] |
| Requests Failed | [count or percentage] |
| Revenue Impact | [if applicable] |
| Services Affected | [service-a, service-b] |

---

## Timeline

All times in UTC. Focus on facts, not assessment.

| Time (UTC) | Event |
|---|---|
| HH:MM | [What happened — objective fact, no blame] |
| HH:MM | Alert fired: [alert name] |
| HH:MM | [Engineer name] acknowledged |
| HH:MM | Incident bridge opened |
| HH:MM | [Investigation step] |
| HH:MM | Root cause identified: [brief description] |
| HH:MM | Remediation applied: [what was done] |
| HH:MM | Alert cleared; service recovering |
| HH:MM | Service fully restored |
| HH:MM | Status page updated — all-clear |

---

## Root Cause

[1–3 paragraphs describing the technical root cause. Be specific. "Database connection pool exhausted due to a query added in PR #1234 that held connections for the full request duration under high load" is better than "database issue."]

### Contributing Factors

These are system conditions that made the incident possible or worse — not causes themselves. Each should be addressable by an action item.

- **[Factor 1]:** [Description — e.g., "No circuit breaker between order-service and payment-service allowed connection exhaustion to cascade"]
- **[Factor 2]:** [e.g., "Alert threshold was 5% error rate; by the time it fired, 30% of requests were failing"]
- **[Factor 3]:** [e.g., "Runbook was outdated and did not include the rollback procedure for this deployment type"]

### What Went Well

[List things that worked as intended — detection systems, response speed, communication, team coordination. Do not omit this section.]

- [e.g., "On-call acknowledged within 2 minutes"]
- [e.g., "Status page was updated before external escalations arrived"]
- [e.g., "Incident bridge communication was clear and focused"]

### What Did Not Go Well

[List gaps in detection, response, tooling, or communication. Be specific and objective.]

- [e.g., "Alert fired 12 minutes after the issue started due to a 10-minute evaluation window"]
- [e.g., "Rollback procedure in the runbook had a broken link to the deploy tool"]
- [e.g., "Secondary on-call was not paged until 20 minutes in; only Tier 1 was configured"]

---

## Action Items

Each action item must have an owner and a deadline. No orphan items.

| Priority | Action | Owner | Due Date | Ticket |
|---|---|---|---|---|
| P1 | [Immediate fix — what will prevent recurrence] | @engineer | YYYY-MM-DD | PROJ-XXX |
| P2 | [Medium-term improvement — alert tuning, runbook update] | @engineer | YYYY-MM-DD | PROJ-XXX |
| P2 | [Add/improve circuit breaker, rate limiter, timeout] | @engineer | YYYY-MM-DD | PROJ-XXX |
| P3 | [Longer-term architectural improvement] | @team | YYYY-MM-DD | PROJ-XXX |

**Action Item Ownership Rules:**
- Every item has exactly one named owner (not a team)
- P1 items due within 1 week
- P2 items due within 1 sprint
- P3 items must be in the backlog and prioritized, not in a document

---

## Lessons Learned

[2–4 sentences synthesizing the key takeaways. What will be different after this postmortem is complete and action items are done? This is not a list — it is a narrative.]

---

## Appendix

### Alert Details
- Alert name: [name]
- Alert query: [query or condition]
- Notification sent to: [rotation name]

### Relevant Logs / Traces

[Links to relevant log searches, trace samples, or dashboard snapshots]

### References

- Runbook: [link]
- PR that introduced the change: [link if applicable]
- Related past incident (if recurrent): [link]
```

---

## Postmortem Facilitation Guide

### Scheduling

- SEV0: within 48 hours of resolution
- SEV1: within 1 week of resolution
- Duration: 30–60 minutes (no longer)
- Attendees: responders + one representative from each affected team; optional for senior leadership

### Facilitator Role

The facilitator is NOT the author. The facilitator:
- Keeps discussion on contributing factors, not individuals
- Redirects blame language: "The engineer didn't notice" → "The alert did not fire before impact exceeded threshold"
- Ensures every contributing factor maps to at least one action item
- Keeps the meeting to time

### Common Blame Patterns to Redirect

| Blame statement | System-focused reframe |
|---|---|
| "Alice should have caught this in review" | "The PR review process did not surface the performance implication" |
| "Bob didn't follow the runbook" | "The runbook was missing the step for this scenario" |
| "The team was slow to respond" | "The escalation policy did not page backup after 15 minutes" |
| "We knew this was a risk" | "The known risk was not converted to a tracked action item" |

### Action Item Quality Check

Before closing the postmortem:
- [ ] Every contributing factor has at least one action item
- [ ] Every action item has an owner and due date
- [ ] P1 items are already in-progress or committed for this sprint
- [ ] Action items are in the ticket tracker (not just in this document)
- [ ] A follow-up review date is set to confirm action items were completed
