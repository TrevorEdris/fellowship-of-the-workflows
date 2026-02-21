# Events API v2

PagerDuty Events API v2 is the primary inbound event channel for all monitoring tool integrations.

**Endpoint:** `POST https://events.pagerduty.com/v2/enqueue`

---

## Request Payload

```json
{
  "routing_key": "<integration_key>",
  "event_action": "trigger",
  "dedup_key": "payments-service:high-error-rate:prod",
  "payload": {
    "summary": "Error rate > 5% for payments-service in prod",
    "severity": "critical",
    "source": "alertmanager.prod.internal",
    "timestamp": "2025-01-15T14:30:00Z",
    "component": "payments-service",
    "group": "payments",
    "class": "error-rate",
    "custom_details": {
      "alert_rule": "HighErrorRate",
      "env": "prod",
      "runbook": "https://wiki.internal/runbooks/payments-error-rate"
    }
  },
  "links": [
    {
      "href": "https://grafana.internal/d/payments",
      "text": "Grafana Dashboard"
    }
  ]
}
```

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `routing_key` | string | Integration key from `pagerduty_service_integration` Terraform output |
| `event_action` | string | `trigger`, `acknowledge`, or `resolve` |
| `payload.summary` | string | Human-readable description (≤1024 chars) |
| `payload.severity` | string | `critical`, `error`, `warning`, or `info` |
| `payload.source` | string | Originating system hostname or identifier |

### Optional but Recommended

| Field | Type | Description |
|-------|------|-------------|
| `dedup_key` | string | Idempotency key; required for acknowledge/resolve |
| `payload.timestamp` | ISO 8601 | Event occurrence time |
| `payload.component` | string | Service component (e.g., `database`, `api`) |
| `payload.group` | string | Logical grouping (e.g., team or service name) |
| `payload.custom_details` | object | Additional key-value metadata |

---

## Severity Values

| PD Severity | Meaning | Creates Incident? |
|-------------|---------|-------------------|
| `critical` | Business-critical, wake someone up | Yes — high urgency |
| `error` | Service degraded, needs prompt attention | Yes — high urgency |
| `warning` | Approaching threshold, watch closely | Yes — low urgency |
| `info` | Informational only | **Never route to PD** |

---

## dedup_key Design

The `dedup_key` controls incident grouping and is required for the acknowledge and resolve actions to affect the correct incident.

### Naming Pattern

```
{service}:{alert_rule}:{env}
```

**Examples:**
- `payments-service:high-error-rate:prod`
- `auth-service:p99-latency-slo-burn:staging`
- `db-primary:replication-lag:prod`

### Rules

- Must be stable across trigger/acknowledge/resolve — all three actions use the same key.
- Scope to alert rule + environment, not to an individual occurrence.
- Do not include timestamps or UUIDs — they prevent deduplication.
- Max 255 characters.

### Lifecycle

```
trigger  (dedup_key: "svc:rule:env")  → creates or re-opens incident
                                            |
acknowledge (same dedup_key)          → moves to acknowledged state
                                            |
resolve  (same dedup_key)             → closes incident, triggers auto-resolve flow
```

If a second `trigger` arrives with the same `dedup_key` while an incident is open, PD appends it as an alert to the existing incident (no new page).

---

## Event Orchestration

Event orchestration is the successor to global rulesets. It is a DAG of rules evaluated top-down.

### Global Orchestration (cross-service routing)

Use for:
- Routing events from a single integration endpoint to multiple services based on payload content
- Applying global suppression windows
- Severity overrides before service-level routing

### Service-Level Orchestration

Use for:
- Suppression windows scoped to a single service (maintenance mode)
- Dynamic severity overrides based on event content
- Custom webhook actions on match

### Rule Evaluation Order

1. Rules are evaluated top-down; first match wins.
2. A rule can `suppress` (drop the event), `route_to` (send to a service), or `set_severity`.
3. A catch-all rule at the bottom prevents events from falling through unrouted.

---

## SDK Usage

### Python (`pdpyras`)

```python
from pdpyras import EventsAPISession

session = EventsAPISession(routing_key="<integration_key>")

# Trigger
session.trigger(
    summary="Error rate > 5% for payments-service",
    source="alertmanager.prod",
    severity="critical",
    dedup_key="payments-service:high-error-rate:prod",
    custom_details={"env": "prod", "runbook": "https://..."}
)

# Resolve
session.resolve(dedup_key="payments-service:high-error-rate:prod")
```

### Go (net/http)

```go
type PDClient struct {
    RoutingKey string
    HTTPClient *http.Client
}

func (c *PDClient) TriggerIncident(dedupKey, summary, severity string) error {
    payload := map[string]interface{}{
        "routing_key":  c.RoutingKey,
        "event_action": "trigger",
        "dedup_key":    dedupKey,
        "payload": map[string]string{
            "summary":  summary,
            "severity": severity,
            "source":   "automation",
        },
    }
    body, _ := json.Marshal(payload)
    req, _ := http.NewRequest("POST", "https://events.pagerduty.com/v2/enqueue", bytes.NewReader(body))
    req.Header.Set("Content-Type", "application/json")
    resp, err := c.HTTPClient.Do(req)
    // handle resp...
    return err
}
```

---

## Webhook Receiver Security

PD sends webhooks on incident state changes. Always verify before processing:

```python
import hmac
import hashlib

def verify_pagerduty_webhook(request_body: bytes, signature_header: str, secret: str) -> bool:
    expected = hmac.new(
        secret.encode(),
        request_body,
        hashlib.sha256
    ).hexdigest()
    received = signature_header.removeprefix("v1=")
    return hmac.compare_digest(expected, received)
```

Idempotency key for webhook processing: `{incident.id}:{event.type}`.
