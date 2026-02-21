# Runbook Template

Every alert that pages a human must have a runbook linked directly in the alert notification body. This template defines the mandatory sections. Copy it, fill in the blanks, delete unused sections.

---

## Template

```markdown
# Runbook: [Alert Name]

**Service:** [service-name]
**Owner Team:** [team-name]
**Alert Condition:** [what metric crossed what threshold — e.g., "Error rate > 1% for 5 minutes"]
**Severity:** SEV[0/1/2/3]
**Last Reviewed:** YYYY-MM-DD
**Reviewer:** [name or @handle]

---

## 1. Alert Meaning

[1–3 sentences: what is firing, why it matters to users, what user experience is impacted]

Example: "This alert fires when the checkout service's HTTP 5xx error rate exceeds 1% for a
5-minute window. Users are actively failing to complete purchases. Revenue impact is direct."

---

## 2. Immediate Triage (First 2 Minutes)

Do these checks before anything else. They distinguish between "recoverable immediately"
and "needs deeper investigation."

1. **Check the dashboard:** [Dashboard URL]
   - Is the spike continuing, recovering, or flat?
   - Which endpoint(s) are failing? (filter by `endpoint` tag)

2. **Check recent deployments:**
   - Was anything deployed in the last 30 minutes?
   - Check: [deployment tool / CI link]

3. **Check upstream dependencies:**
   - Database: [Postgres/MySQL/etc. dashboard link]
   - Cache: [Redis/Memcached dashboard link]
   - External APIs: [third-party status pages]

4. **Verify alert is real:** [Link to metric query to confirm the alert is not a monitoring glitch]

---

## 3. Common Causes and Remediation

### Cause A: Recent Bad Deployment

**Indicators:**
- Alert started within 5 minutes of a deploy
- Error traces show new code path or changed function name

**Remediation:**
1. Identify the deploy: `[command to list recent deploys]`
2. Initiate rollback: `[rollback command or link to runbook section]`
3. Verify recovery: watch error rate drop below 0.5% for 2+ minutes

---

### Cause B: Downstream Dependency Failure

**Indicators:**
- Errors concentrated in one endpoint that calls [database/service]
- Upstream service has its own active alert

**Remediation:**
1. Confirm upstream outage via their status or alert
2. If upstream owns the failure: escalate to their on-call via [escalation path]
3. If circuit breaker available: enable it to degrade gracefully — `[command]`
4. Update status page: "Order service degraded due to upstream dependency"

---

### Cause C: Traffic Spike / Overload

**Indicators:**
- Error rate rising with request rate
- P99 latency spiking simultaneously
- No recent deploy

**Remediation:**
1. Check autoscaler status: `[command]`
2. Manually scale if autoscaler is lagging: `[command]`
3. Enable rate limiting if configured: `[command or config toggle]`
4. Shed non-critical traffic if possible (disable [feature X] toggle)

---

### Cause D: [Custom Cause]

[Add project-specific causes here. Every runbook should have at least 2–3 causes documented from past incidents.]

---

## 4. Escalation Criteria

Escalate to Tier 2 / Engineering Manager if:
- [ ] Alert has not cleared after 15 minutes of active remediation
- [ ] You cannot identify the root cause from dashboards and logs
- [ ] The rollback did not resolve the issue
- [ ] A downstream team is not responding within 10 minutes
- [ ] User-visible impact extends to [percentage] or [absolute user count]

---

## 5. Rollback Procedure

**Prerequisite:** Confirm current version: `[command to get current deploy version]`

```bash
# Step 1: Identify the last known-good version
[command or link to deployment history]

# Step 2: Initiate rollback
[rollback command]

# Step 3: Verify rollback is in progress
[command to check deploy status]

# Step 4: Monitor recovery
# Watch error rate on dashboard — expect recovery within 3–5 minutes of rollback complete
```

**If rollback fails or makes things worse:**
1. Do not rollback the rollback without consulting senior engineer
2. Escalate immediately
3. Consider: does the issue predate the deploy? (Check metrics from prior to the deploy)

---

## 6. Post-Incident Actions

After the alert clears:
- [ ] Update incident ticket/channel with root cause summary
- [ ] File a follow-up ticket if the root cause is not fully resolved
- [ ] Update this runbook if any step was wrong or missing
- [ ] Schedule postmortem if SEV0 or SEV1 (within 48h for SEV0, 1 week for SEV1)
- [ ] Notify stakeholders via status page update

**Postmortem required:** SEV0 (always) | SEV1 (always) | SEV2 (if recurrent, same cause 3+ times)

---

## Related Resources

- **Dashboard:** [URL]
- **Service repository:** [URL]
- **Dependencies:** [list with runbook links]
- **Status page:** [URL]
- **Incident channel:** `#incidents-[service-name]`
- **Team Slack:** `#team-[team-name]`
```

---

## Runbook Review Checklist

Before publishing a new runbook or after updating an existing one:

- [ ] Every step is actionable without additional context
- [ ] Commands are copy-pasteable (no placeholders left unfilled)
- [ ] All URLs are reachable without VPN if responder is remote
- [ ] A person unfamiliar with the service can complete triage steps in < 2 minutes
- [ ] Common causes cover at least 80% of historical incidents for this alert
- [ ] Escalation criteria are specific (not "if unsure, escalate")
- [ ] Rollback procedure is verified (not theoretical)
- [ ] Last reviewed date is within 90 days
