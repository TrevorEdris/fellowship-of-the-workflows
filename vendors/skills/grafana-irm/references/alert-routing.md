# Grafana IRM — Alert Routing Reference

Covers integration setup, alert source configuration, and escalation chain design patterns.

---

## Alert Sources Supported

| Source | Integration Type | Setup Location |
|---|---|---|
| Grafana Alerting (native) | `grafana` | Auto-configured via Grafana UI; IRM enabled in stack settings |
| Prometheus Alertmanager | `alertmanager` | Alertmanager `receivers` config → webhook URL |
| Grafana OnCall API | `webhook` | HTTP POST with JSON payload |
| Email | `email` | SMTP-forwarded alerts |
| PagerDuty (inbound) | `pagerduty` | PagerDuty global event routing → IRM endpoint |

---

## Alertmanager → Grafana IRM

Configure Alertmanager to forward alerts to Grafana IRM via webhook:

```yaml
# alertmanager.yml
global:
  resolve_timeout: 5m

route:
  receiver: grafana-irm-default
  group_by: ['alertname', 'service', 'severity']
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 4h

  routes:
    - match:
        severity: critical
      receiver: grafana-irm-critical
      continue: false

    - match:
        severity: warning
      receiver: grafana-irm-default

receivers:
  - name: grafana-irm-critical
    webhook_configs:
      - url: '{{ env "GRAFANA_IRM_CRITICAL_WEBHOOK_URL" }}'
        send_resolved: true
        http_config:
          bearer_token: '{{ env "GRAFANA_IRM_API_TOKEN" }}'

  - name: grafana-irm-default
    webhook_configs:
      - url: '{{ env "GRAFANA_IRM_DEFAULT_WEBHOOK_URL" }}'
        send_resolved: true
```

The webhook URL comes from `grafana_oncall_integration.link` in Terraform output.

---

## Grafana Alerting (Native) → IRM

When using Grafana Alerting (unified alerting in Grafana Cloud):

1. Navigate to: **Alerting → Contact points**
2. Create a new contact point of type **"Grafana OnCall"**
3. Select your IRM integration from the dropdown
4. Assign the contact point to a notification policy

```yaml
# Grafana alerting notification policy (API/provisioning format)
apiVersion: 1
policies:
  - receiver: grafana-irm-platform
    matchers:
      - severity =~ "critical|high"
    group_by: ['alertname', 'service']
    group_wait: 30s
    group_interval: 5m
    repeat_interval: 4h
    continue: false
  - receiver: grafana-irm-default
```

---

## Escalation Chain Patterns

### Pattern 1: Standard Three-Tier (Recommended for Most Teams)

```
Immediate: Notify primary on-call schedule
Wait 5m:   If unacknowledged, notify secondary schedule
Wait 10m:  If still unacknowledged, notify engineering manager (named user)
```

See `terraform-irm.md` for the Terraform implementation.

### Pattern 2: Critical Fast-Escalation

For SEV0 services where 5-minute delay before secondary is too slow:

```
Immediate: Notify primary on-call schedule
Wait 2m:   Notify secondary on-call schedule simultaneously
Wait 10m:  Notify engineering manager
Trigger webhook: Post to #sev0-incidents Slack channel
```

### Pattern 3: Business-Hours Only (SEV2/3)

For lower-severity alerts that do not require after-hours response:

```
Check: Is current time within business hours (09:00-18:00 local)?
  Yes → Notify primary on-call
  No  → Create ticket only; no page
```

Note: Grafana IRM supports time-based routing via schedule overrides and "quiet hours" but does not have a native "business hours only" escalation step. Implement via Alertmanager routing rules with time_intervals instead.

---

## Routing Regex Patterns

`grafana_oncall_route.routing_regex` matches against the raw alert label string.

```hcl
# Match alerts from a specific service
routing_regex = "service=order-service"

# Match critical severity
routing_regex = "severity=critical"

# Match either critical or high
routing_regex = "severity=(critical|high)"

# Match alerts with specific label
routing_regex = "team=platform"

# Catch-all (default route — no regex needed, position = highest number)
# Leave routing_regex empty for default route
```

---

## Slack ChatOps Workflow

When Slack integration is enabled:

1. Alert fires → IRM creates an alert group
2. Slack message posted to configured channel with:
   - Alert name and labels
   - Acknowledge / Resolve / Silence buttons
   - Link to IRM incident page
3. On-call engineer acknowledges via Slack button (no need to log in to Grafana)
4. If resolved via runbook: mark resolved in Slack; IRM closes the incident

**Required Slack App Permissions:**
- `chat:write`
- `channels:read`
- `users:read`
- `users:read.email`

---

## Maintenance Windows (Silences)

Create silences in Grafana Alerting to prevent noise during deployments:

```bash
# Via Grafana API — create a silence
curl -X POST \
  "${GRAFANA_URL}/api/alertmanager/grafana/api/v2/silences" \
  -H "Authorization: Bearer ${GRAFANA_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "matchers": [
      {"name": "service", "value": "order-service", "isRegex": false}
    ],
    "startsAt": "2026-03-10T02:00:00Z",
    "endsAt": "2026-03-10T04:00:00Z",
    "comment": "Planned maintenance window for schema migration",
    "createdBy": "platform-team"
  }'
```

Always set silences before the maintenance window starts, not during a live issue.
