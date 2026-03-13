# Severity Mapping

Map monitoring tool alert severity to PagerDuty severity consistently. Inconsistent mapping is the primary cause of alert fatigue.

---

## PagerDuty Severity Values

| PD Severity | Meaning | Notification Urgency |
|-------------|---------|---------------------|
| `critical` | Business-critical failure, customer-facing impact | High — immediate page |
| `error` | Service degraded, needs prompt attention | High — immediate page |
| `warning` | Approaching thresholds, preemptive | Low — no immediate page |
| `info` | Informational only | **Never route to PD** |

---

## AlertManager → PagerDuty

AlertManager labels map to PD severity in the `pagerduty_configs` receiver:

```yaml
# alertmanager.yaml
receivers:
  - name: pagerduty-critical
    pagerduty_configs:
      - routing_key: "<integration_key_from_terraform>"
        severity: '{{ if eq .CommonLabels.severity "page" }}critical{{ else if eq .CommonLabels.severity "ticket" }}warning{{ else }}info{{ end }}'
        description: '{{ .CommonAnnotations.summary }}'
        details:
          alert_rule: '{{ .CommonLabels.alertname }}'
          service: '{{ .CommonLabels.service }}'
          env: '{{ .CommonLabels.env }}'
          runbook: '{{ .CommonAnnotations.runbook_url }}'
        client: alertmanager
        client_url: '{{ .ExternalURL }}'
        # dedup_key — AlertManager sends alert fingerprint as dedup key by default.
        # Override for stable keys:
        group_key: '{{ .GroupLabels.service }}:{{ .GroupLabels.alertname }}:{{ .GroupLabels.env }}'

route:
  receiver: default-receiver
  routes:
    - match:
        severity: page
      receiver: pagerduty-critical
    - match:
        severity: ticket
      receiver: pagerduty-warning
    - match:
        severity: info
      receiver: slack-only  # Never route info to PD
```

### AlertManager Severity Label → PD Severity

| AlertManager Label | PD Severity | Creates PD Incident? |
|--------------------|-------------|---------------------|
| `severity: page` | `critical` | Yes — high urgency |
| `severity: ticket` | `warning` | Yes — low urgency |
| `severity: info` | `info` | **No — suppress before reaching PD** |
| (no label) | `error` | Yes — high urgency |

---

## Datadog → PagerDuty

Datadog uses a named PD service integration (`@pagerduty-{service-name}`) in monitor message blocks:

```hcl
# Datadog monitor Terraform
resource "datadog_monitor" "payments_error_rate" {
  name  = "payments-service error rate high"
  type  = "metric alert"
  query = "sum(last_5m):sum:trace.web.request.errors{service:payments-service,env:prod}.as_count() / sum:trace.web.request.hits{service:payments-service,env:prod}.as_count() > 0.05"

  message = <<-EOT
    Error rate exceeded 5% on {{service.name}} in {{env.name}}.
    Runbook: https://wiki.internal/runbooks/payments-error-rate
    @pagerduty-payments-service
  EOT

  thresholds = {
    critical = 0.05   # → PD critical (triggers high-urgency page)
    warning  = 0.02   # → PD warning (low-urgency notification)
  }

  notify_no_data    = false
  renotify_interval = 0   # Do not re-notify — PD handles escalation
}
```

The `@pagerduty-{name}` handle maps to the Datadog integration configured on the PD service. The name must match exactly what is configured in the PD Datadog integration.

### Datadog Threshold → PD Severity

| Datadog Threshold State | PD Severity | Urgency |
|------------------------|-------------|---------|
| `ALERT` (critical threshold) | `critical` | High |
| `WARN` (warning threshold) | `warning` | Low |
| `OK` | *(sends resolve)* | — |
| `NO DATA` | Configurable — typically suppress | — |

**Rule:** Never set `notify_no_data: true` and route to PD without first verifying the monitor reliably receives data. No-data pages are a leading source of false positives.

---

## Grafana → PagerDuty

```yaml
# Grafana contact point (via Grafana provisioning)
apiVersion: 1
contactPoints:
  - orgId: 1
    name: PagerDuty Payments
    receivers:
      - uid: pd-payments
        type: pagerduty
        settings:
          integrationKey: "<integration_key>"
          severity: "{{ .CommonLabels.severity }}"
          class: "{{ .CommonLabels.alertname }}"
          component: "{{ .CommonLabels.service }}"
          group: "{{ .CommonLabels.namespace }}"
          dedupKey: "{{ .GroupLabels.service }}:{{ .GroupLabels.alertname }}:{{ .CommonLabels.env }}"
```

---

## Noise Tiering: Three-Tier Routing

Every alert must be classified into one of three tiers before it reaches PD:

| Tier | Route To | PD Urgency | Use Case |
|------|----------|-----------|----------|
| **Page** | PD P1/P2 incident | High | SLO burn rate exhaustion, customer-facing error rate |
| **Notify** | Slack channel + PD low-urgency | Low | Approaching thresholds, early warning signals |
| **Log** | Monitoring tool dashboard only | None | Internal metrics, capacity planning data |

**Rule:** Never route tier-3 (log) alerts to PD under any circumstances. Log-tier alerts should never even appear in AlertManager routes that go to PD.

### Decision Tree

```
Does this alert indicate a symptom visible to customers?
├── Yes → Is it currently causing customer impact?
│         ├── Yes → Page (PD high urgency, P1/P2)
│         └── No (approaching threshold) → Notify (PD low urgency)
└── No → Is it a leading indicator a human should investigate today?
          ├── Yes → Notify (Slack only)
          └── No → Log (monitoring tool only)
```

---

## Common Mapping Anti-Patterns

| Anti-Pattern | Why It Hurts | Fix |
|-------------|-------------|-----|
| Routing `info` to PD | Floods PD with non-actionable events | Suppress before routing |
| Using CPU/memory as page triggers | Cause-based, not symptom-based; high false positive rate | Page on error rate and latency |
| No `dedup_key` on trigger events | Flapping creates duplicate incidents | Always set `dedup_key` |
| `notify_no_data: true` on Datadog → PD | No-data is often a monitoring gap, not a real failure | Suppress no-data or route to Slack only |
| Same severity for all alerts in a service | Engineers learn to ignore pages | Use `critical` sparingly; reserve for true customer impact |
