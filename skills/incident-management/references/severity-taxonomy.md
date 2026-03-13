# Severity Taxonomy (Platform-Agnostic)

Standard severity levels and escalation policy structure. These definitions are platform-independent and should be mapped to your platform's native severity labels during setup.

---

## Severity Level Definitions

| Level | Definition | User Impact | Response | Example |
|---|---|---|---|---|
| **SEV0 / P0** | Total service failure; all users impacted | Complete outage | Immediate page; incident bridge now | Payment service down; login impossible |
| **SEV1 / P1** | Significant degradation; majority impacted | Severely degraded | Page; 15-min response SLA | Checkout latency 10x normal |
| **SEV2 / P2** | Partial failure; subset of users or features impacted | Noticeable degradation | Ticket; next-business-hour response | Background job failures, one region degraded |
| **SEV3 / P3** | Minor anomaly; no user impact | None currently | Ticket; scheduled review | Slow query trending upward, disk at 70% |

### Platform Mapping Reference

| FotW Level | Grafana IRM | incident.io | Better Stack | PagerDuty | Datadog |
|---|---|---|---|---|---|
| SEV0 | Critical | Critical | Critical | P1 | Critical |
| SEV1 | High | High | High | P2 | High |
| SEV2 | Medium | Medium | Medium | P3 | Medium |
| SEV3 | Low | Low | Low | P4 | Low |

---

## Standard Escalation Policy (Three-Tier)

```
Tier 1: On-call primary
  → Notified immediately on SEV0/SEV1
  → Response SLA: 5 minutes

Tier 2: On-call secondary (backup)
  → Escalated if Tier 1 does not acknowledge within 5 minutes
  → Fallback: secondary verifies primary is reachable or takes over

Tier 3: Engineering Manager
  → Escalated if Tier 2 does not acknowledge within 10 minutes
  → Action: delegate to available engineer or declare incident bridge

Tier 4: VP / Director / Incident Commander
  → Escalated after 30 minutes total for SEV0/SEV1 only
  → Action: authorize escalation resources, communicate to stakeholders
```

### Escalation Configuration Fields (Any Platform)

| Field | Recommended Value |
|---|---|
| Tier 1 acknowledge SLA | 5 minutes |
| Tier 2 escalation delay | 5 minutes after Tier 1 notification |
| Tier 3 escalation delay | 15 minutes after initial notification |
| Tier 4 escalation delay | 30 minutes after initial notification (SEV0/1 only) |
| SEV2/P2 escalation | Tier 1 notify only; no auto-escalation |
| SEV3/P3 escalation | None; ticket routing only |

---

## Incident Response Protocol by Severity

### SEV0 — Total Outage

1. **T+0:** On-call paged; acknowledge within 5 minutes
2. **T+2:** Open incident bridge (Slack channel, Zoom/Meet)
3. **T+5:** Assess blast radius; consider rollback
4. **T+10:** Stakeholder communication sent (status page update + internal Slack)
5. **T+15:** If not resolved, incident commander assigned
6. **T+30:** Executive escalation if SEV0 persists
7. **Resolution:** Update status page, send all-clear, schedule postmortem within 48h

### SEV1 — Significant Degradation

1. **T+0:** On-call paged; acknowledge within 5 minutes
2. **T+5:** Begin triage; runbook consulted
3. **T+15:** Incident channel opened if multiple people needed
4. **T+20:** Status page update if user-visible
5. **Resolution:** Postmortem within 1 week

### SEV2 — Partial Failure

1. Create Jira/Linear ticket with impact description
2. Assign to owning team
3. Resolve within next sprint
4. Document root cause in ticket; no formal postmortem required unless recurrent

### SEV3 — Minor Anomaly

1. Create ticket; add to backlog
2. Review in next sprint planning
3. No immediate action required

---

## Severity Classification Decision Tree

```
Is any user-visible functionality completely unavailable?
├── Yes → Is it all users or a majority? → SEV0
└── No
    └── Is response time degraded > 5x baseline for majority of users?
        ├── Yes → SEV1
        └── No
            └── Are a subset of users or features affected?
                ├── Yes → SEV2
                └── No → SEV3 (internal anomaly only)
```

---

## Common Mistakes to Avoid

| Mistake | Why It's Harmful | Correct Approach |
|---|---|---|
| Over-classifying as SEV0/1 | Alert fatigue; on-call distrust | SEV0 = full outage only; be strict |
| Under-classifying to avoid process overhead | User impact lingers; no postmortem | Err on higher severity; downgrade after triage |
| No severity on internal tickets | Can't prioritize or filter | Always classify, even for SEV3 |
| Changing severity during incident | Confuses responders | Classify once at detection; add note if wrong |
