# Alert Noise Reduction

Alert fatigue is the leading cause of on-call burnout and missed incidents. Apply these patterns in order — each layer reduces noise before it reaches the next.

---

## Noise Reduction Layers

```
Layer 1: Monitoring tool (AlertManager / Datadog)
  - Inhibition rules, grouping, for: duration requirements
  - Goal: prevent sub-threshold flapping from generating any alert

Layer 2: PagerDuty event orchestration
  - Severity overrides, global suppression rules
  - Goal: catch anything that leaked through layer 1

Layer 3: PagerDuty service-level settings
  - Alert grouping (time-based), dedup_key matching
  - Goal: collapse related alerts into one incident

Layer 4: Escalation policy hygiene
  - Notification rules, urgency mapping
  - Goal: right person, right time, right channel
```

Never rely on PD as the first and only noise reduction layer.

---

## Pattern 1: Page on Symptoms, Not Causes

**Page on:**
- Error rate > threshold (customer-facing impact)
- P99 latency > SLO threshold (customer experience)
- SLO burn rate exceeding budget (time-to-exhaustion critical)
- Service completely unavailable (health check failure)

**Never page on:**
- CPU utilization > 80% (may be normal load; page on latency instead)
- Memory usage > 70% (page on OOM errors or request failures instead)
- Disk usage > 85% (page only if < 2 hours to full; otherwise notify)
- Pod restart count (page on error rate caused by restarts, not the restart itself)

---

## Pattern 2: Flapping Suppression

A flapping alert fires, resolves, fires again within minutes. Each cycle creates a new incident.

### AlertManager: `for` Duration

```yaml
groups:
  - name: payments
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m]) > 0.05
        for: 2m  # Must stay above threshold for 2 continuous minutes before firing
        labels:
          severity: page
        annotations:
          summary: "Error rate > 5% for {{ $labels.service }}"
```

The `for: 2m` requirement prevents alerts that spike and recover within 2 minutes from reaching PD.

### Stable `dedup_key`

A flapping alert with a stable `dedup_key` creates one incident, then re-triggers it (appending alerts) rather than creating new incidents. This requires `dedup_key` to be set consistently across trigger/resolve cycles.

```
Alert flaps: trigger → resolve → trigger → resolve
With stable dedup_key:  1 incident created → closed → re-opened → closed
Without dedup_key:      4 separate incidents, 4 pages
```

---

## Pattern 3: AlertManager Inhibition Rules

Inhibit lower-priority alerts when a higher-priority alert is already firing for the same service. Prevents cascade pages when a single root cause triggers multiple rules.

```yaml
inhibit_rules:
  - source_match:
      alertname: ServiceDown
    target_match_re:
      alertname: HighLatency|HighErrorRate|DatabaseConnectionError
    equal: [service, env]
    # When ServiceDown fires for payments-service:prod,
    # suppress HighLatency and HighErrorRate for the same service+env
```

### Common Inhibition Patterns

| Source (Higher Priority) | Suppress (Lower Priority) | Equal Labels |
|--------------------------|--------------------------|--------------|
| `ServiceDown` | `HighErrorRate`, `HighLatency` | `service`, `env` |
| `DatabaseDown` | `DatabaseSlowQuery`, `DatabaseConnectionError` | `database`, `env` |
| `NodeNotReady` | all pod-level alerts | `node` |

---

## Pattern 4: Alert Grouping in PagerDuty

Time-based grouping: any alerts from the same PD service arriving within the configured window are grouped into one incident.

```hcl
resource "pagerduty_service" "payments" {
  alert_grouping_parameters {
    type = "time"
    config {
      timeout = 300  # 5-minute window — tune based on cascade timing
    }
  }
}
```

**When to increase the window:**
- Cascading failures regularly produce 10+ alerts within 10 minutes → use 600s
- Multiple monitoring tools alert on the same event with slight timing offsets → use 300s

**When to disable grouping:**
- Each alert from this service is always a distinct, independent incident

---

## Pattern 5: Suppression Windows (Maintenance Mode)

Create a maintenance window before any planned downtime:

```bash
# Via PagerDuty API
curl -X POST "https://api.pagerduty.com/maintenance_windows" \
  -H "Authorization: Token token=$PD_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "maintenance_window": {
      "type": "maintenance_window",
      "start_time": "2025-03-01T02:00:00Z",
      "end_time": "2025-03-01T04:00:00Z",
      "description": "Scheduled database migration",
      "services": [{"id": "P1AB2CD", "type": "service_reference"}]
    }
  }'
```

```hcl
# Via Terraform (for recurring windows, use CI/CD to apply before deployment)
resource "pagerduty_maintenance_window" "weekly_deploy" {
  start_time  = "2025-03-01T02:00:00Z"
  end_time    = "2025-03-01T04:00:00Z"
  description = "Weekly deployment window"
  services    = [pagerduty_service.payments.id]
}
```

---

## Pattern 6: Escalation Policy Hygiene

An over-escalated policy pages more people than necessary, training engineers to deprioritize pages.

- Maximum 3 escalation levels per policy.
- L1 timeout: 5 minutes — short enough to catch sleeping engineers, long enough to not escalate immediately for brief distraction.
- L2 timeout: 15 minutes — team lead has time to context-switch.
- After L2, escalation is organizational signaling, not technical response.
- `num_loops = 1` (repeat policy once): prevents infinite paging on truly unacknowledged incidents.

---

## Noise Audit Checklist

Run this audit monthly:

- [ ] How many incidents were created last month? How many were P1/P2?
- [ ] Which services created the most incidents? Are they all actionable?
- [ ] What percentage of incidents were auto-resolved without human action?
- [ ] How many incidents had a `resolve` event within 5 minutes of `trigger`? (Flapping indicator)
- [ ] Are any alerts routing `info` severity to PD?
- [ ] Are any Datadog monitors using CPU/memory as page triggers?
- [ ] Do all AlertManager rules have `for: >= 2m`?
- [ ] Are all PD services using alert grouping?
