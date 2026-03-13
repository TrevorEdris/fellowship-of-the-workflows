# On-Call Rotation Patterns

Platform-agnostic on-call design. These patterns apply equally to Grafana IRM, incident.io, Better Stack, and PagerDuty.

---

## Prerequisites Before Going On-Call

**Minimum viable rotation requires:**
- At least 4 engineers in the pool (fewer = unsustainable burnout risk)
- Each engineer has access to all runbooks for their service scope
- Each engineer can access production systems independently (no approval blockers during incidents)
- Escalation paths are documented and tested (not just configured)

**Before the first rotation:**
- [ ] All runbooks reviewed by at least one engineer who didn't write them
- [ ] Incident response drills completed (at least one tabletop exercise)
- [ ] Shadow rotation completed for new engineers
- [ ] Escalation chain verified end-to-end (page Tier 1 → verify Tier 2 escalates correctly)

---

## Rotation Patterns

### Standard Weekly Rotation

```
Monday 09:00 → Monday 09:00 (next week)
Primary on-call: 1 engineer per shift
Secondary on-call: 1 engineer (backup, escalation Tier 2)
```

Best for: teams of 4–8 engineers in overlapping timezones.

**Handoff checklist (synchronous, Monday morning):**
1. Active incidents: status, owner, next steps
2. Monitors recently firing (last 7 days): explain any suppressions
3. Known noisy alerts: which ones are being investigated
4. Upcoming deployments or changes this week
5. Any alerts that were tuned during the shift (document why)

### Follow-the-Sun (Global Teams)

Three timezone bands with 8-hour overlapping shifts:

```
AMER band:  09:00–18:00 ET  (UTC-5 to UTC-8)
EMEA band:  09:00–18:00 CET (UTC+1 to UTC+3)
APAC band:  09:00–18:00 JST (UTC+9)
```

**Handoff cadence:** Daily at band boundary; synchronous 15-minute call or written status.

**Required for follow-the-sun:**
- Incident channel with full context visible to all bands (Slack with persistent history)
- Status written before handoff (not just verbal)
- Incident commander role transfers explicitly

### Shadow Rotation (Mentorship)

Pair each junior engineer with a senior for 2–4 rotation cycles before solo on-call:

```
Shadow rotation: Junior + Senior both paged
  - Junior responds first; Senior observes
  - Senior intervenes only if Junior is stuck > 10 minutes
  - Debrief after every incident, even minor ones
```

**Graduation criteria:**
- Handled at least 3 SEV2 incidents independently (with shadow watching)
- Handled at least 1 SEV1 incident from start to resolution
- Can locate any runbook in < 60 seconds
- Can access and read relevant dashboards without assistance

---

## Rotation Schedules by Team Size

| Team Size | Rotation Pattern | Weekly On-Call Burden |
|---|---|---|
| 3 engineers | Not sustainable; hire before enabling rotation | — |
| 4 engineers | 1-week shifts, no secondary | 25% (1 in 4 weeks) |
| 5–6 engineers | 1-week shifts with secondary | ~17–20% |
| 7–8 engineers | 1-week shifts with secondary + escalation shadow | ~12–14% |
| 9+ engineers | 2-week shifts feasible; shadow rotation recommended | < 12% |

---

## On-Call Compensation and Health

These are organizational policies, not tool configurations, but they matter for rotation sustainability:

- **On-call allowance:** Compensate engineers for being on-call, even if no pages fire.
- **Incident time:** Time spent on incidents outside business hours counts toward workload; adjust sprint capacity.
- **Recovery time:** Engineers who respond to a SEV0 outside business hours get the equivalent time off.
- **PTO coverage:** On-call must be explicitly covered during PTO, not left to chance. Set this in the rotation tool as a hard override, not a verbal arrangement.
- **Holiday rotations:** Build holiday coverage into the schedule at the start of each quarter.

---

## Configuration Templates

### Escalation Policy YAML (Generic — translate to platform)

```yaml
escalation_policy:
  name: "platform-team-standard"
  steps:
    - delay_minutes: 0
      targets:
        - type: schedule
          id: primary-on-call-schedule
    - delay_minutes: 5
      targets:
        - type: schedule
          id: secondary-on-call-schedule
    - delay_minutes: 15
      targets:
        - type: user
          id: engineering-manager
    - delay_minutes: 30
      targets:
        - type: user
          id: vp-engineering
      conditions:
        - severity: ["sev0", "sev1"]  # Tier 4 for SEV0/1 only
```

### Schedule Rotation YAML (Generic)

```yaml
schedule:
  name: "primary-on-call"
  timezone: "America/New_York"
  rotation:
    type: weekly
    start_day: monday
    start_time: "09:00"
    users:
      - alice
      - bob
      - charlie
      - diana
  overrides: []  # PTO overrides added here
```

---

## Runbook Readiness Review

Run before each rotation cycle (especially after new engineers join):

```
For each runbook in the service scope:
  1. Is the runbook reachable from the alert notification?
  2. Is the runbook accurate (last reviewed < 90 days)?
  3. Does the runbook include escalation criteria?
  4. Does it include rollback steps?
  5. Is there a known-bad pattern section?
```

**Runbook staleness signals:**
- References services or tools that no longer exist
- Remediation steps that require permissions the on-call engineer doesn't have
- No "last reviewed" date in the header
- Written only by the author of the feature (single-author knowledge)
