# Better Stack — Monitors and Alerting Reference

Covers monitor configuration, on-call policy design, alert suppression, and MCP usage.

---

## Monitor Design Principles

The same symptom-based alerting principles apply in Better Stack. Configure monitors to detect user-visible impact:

| Monitor Type | What to Monitor | When to Page |
|---|---|---|
| HTTP status | `/healthz` endpoint returns 2xx | Non-2xx for > 3 minutes |
| Keyword | Response body contains expected content | Keyword absent for > 3 minutes |
| SSL | Certificate expiry | < 30 days remaining |
| TCP | Database / cache port open | Port closed for > 1 minute |
| Cron | Heartbeat received within expected window | No heartbeat received |

**Confirmation period:** Set to 180 seconds (3 minutes) minimum. This prevents false-positive pages from transient network blips. Adjust up (to 5 minutes) for services with longer health check startup windows.

**Recovery period:** Set to 180 seconds minimum. Prevents "flapping" pages where a monitor recovers and re-alerts repeatedly.

---

## Multi-Region Monitoring

Always check from multiple regions. A failure in only one region may indicate:
- CDN routing issue (not a service outage)
- Regional infrastructure failure (real incident, but geographically scoped)
- The check region itself having network issues (false positive)

Recommended regions:
- `us` — North America (Virginia)
- `eu` — Europe (Amsterdam or Frankfurt)
- `ap` — Asia-Pacific (Singapore or Tokyo)

**Alerting rule:** Alert when a monitor fails from ≥ 2 regions simultaneously to filter single-region false positives.

```hcl
resource "betterstack_monitor" "api" {
  monitor_type    = "status"
  url             = "https://api.example.com/healthz"
  name            = "API Health"
  regions         = ["us", "eu", "ap"]

  # Only alert if failing from multiple locations
  # (Better Stack UI: "Alert when failing from" → "2 or more locations")
  confirmation_period = 180
}
```

---

## On-Call Policy Design

### Minimum Viable On-Call Setup

```
Primary escalation policy:
  Step 1: Notify current on-call engineer (immediately)
  Step 2: Notify backup engineer (after 5 minutes)
  Step 3: Notify all team members (after 15 minutes)
  Repeat: 2 times before giving up (total 45 minutes of escalation)
```

### Business Hours vs. After-Hours

Better Stack supports "quiet hours" per escalation policy — suppressing phone calls and SMS during off-hours while still sending push/email:

```
Weekdays 09:00–18:00 (team timezone): Full escalation (push + SMS + call)
Weekdays 18:00–09:00: Push only (no SMS, no call) for SEV2/3
Weekends: Push only for SEV2/3; full escalation for SEV0/1
```

Configure via **On-Call → Policies → [Policy] → Quiet Hours**.

### On-Call Rotation Best Practices

- Minimum 4 engineers before enabling primary rotation
- 1-week shifts with Monday morning handoff (synchronous, not async)
- Always configure a secondary/backup calendar before going live
- Test the escalation chain end-to-end before first shift (page yourself, confirm you receive the notification, confirm escalation fires)

---

## Alert Suppression and Maintenance Windows

### Maintenance Windows (Temporary Silences)

Before planned maintenance, create a maintenance window to suppress alerts:

1. **Better Stack UI:** Monitors → [Monitor] → Maintenance → Schedule Maintenance
2. Set start/end time, description, and affected monitors

**API:**
```bash
curl -X POST \
  "https://uptime.betterstack.com/api/v2/maintenance-windows" \
  -H "Authorization: Bearer ${BETTER_STACK_API_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Database migration window",
    "start_at": "2026-03-10T02:00:00Z",
    "end_at": "2026-03-10T04:00:00Z",
    "monitor_ids": ["monitor_id_1", "monitor_id_2"]
  }'
```

### Alert Pausing

For indefinite pauses (during investigation), pause a monitor directly:

```bash
curl -X PATCH \
  "https://uptime.betterstack.com/api/v2/monitors/MONITOR_ID" \
  -H "Authorization: Bearer ${BETTER_STACK_API_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"paused": true}'
```

Always resume after the investigation is complete.

---

## MCP Server Usage

The Better Stack MCP server covers incidents, on-call, log queries, and postmortem drafting.

**Announcement:** https://betterstack.com/community/blog/changelog-12-mcp-server/

### Connection Setup

```json
// Claude Desktop config
{
  "mcpServers": {
    "better-stack": {
      "url": "https://uptime.betterstack.com/mcp",
      "headers": {
        "Authorization": "Bearer YOUR_BETTER_STACK_API_TOKEN"
      }
    }
  }
}
```

### Available Tools

| Tool | What It Does |
|---|---|
| `list_incidents` | List active and recent incidents |
| `get_incident` | Get incident details and timeline |
| `create_incident` | Manually declare an incident |
| `list_monitors` | List all monitors and their status |
| `get_monitor` | Get a specific monitor's status and history |
| `get_who_is_on_call` | Identify the current on-call engineer |
| `list_escalation_policies` | List configured escalation policies |
| `query_logs` | Query Better Stack logs (Loki-compatible LogQL) |
| `draft_postmortem` | AI-generated postmortem draft from incident data |

### Example AI Workflows

```
"What monitors are currently down?"
→ list_monitors() → filter for status=down

"Who is on-call right now?"
→ get_who_is_on_call()

"Query logs for errors in order-service in the last 30 minutes"
→ query_logs(query='{service="order-service"} |= "error"', range="30m")

"Draft a postmortem for the incident that occurred today"
→ list_incidents() → get_incident() → draft_postmortem()
```

---

## Webhook Integration

Better Stack can send alert webhooks to any endpoint for custom integrations:

```bash
# Sample webhook payload structure (sent by Better Stack on alert)
{
  "monitor": {
    "id": "12345",
    "url": "https://api.example.com/healthz",
    "name": "API Health Check",
    "status": "down"
  },
  "incident": {
    "id": "inc_abc123",
    "started_at": "2026-03-15T14:30:00Z",
    "cause": "Monitor is DOWN"
  }
}
```

Configure webhooks in **Monitors → [Monitor] → Settings → Notifications → Add webhook**.
