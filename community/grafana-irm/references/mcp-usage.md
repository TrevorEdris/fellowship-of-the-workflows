# Grafana IRM — MCP Usage Reference

The `grafana/mcp-grafana` MCP server provides AI-native access to Grafana dashboards, alerts, and IRM operations. It is the official MCP server from Grafana Labs.

**Repository:** https://github.com/grafana/mcp-grafana
**Covers:** Grafana Alerting, Grafana IRM (OnCall + Incident), dashboards, Loki logs

---

## Installation

### Claude Desktop / Claude Code

```json
// ~/.claude/claude_desktop_config.json or MCP settings
{
  "mcpServers": {
    "grafana": {
      "command": "mcp-grafana",
      "args": [],
      "env": {
        "GRAFANA_URL": "https://your-stack.grafana.net",
        "GRAFANA_API_KEY": "your-service-account-token"
      }
    }
  }
}
```

Install the binary:
```bash
go install github.com/grafana/mcp-grafana/cmd/mcp-grafana@latest
# OR
brew install grafana/tap/mcp-grafana
```

### Cursor

```json
// .cursor/mcp.json
{
  "mcpServers": {
    "grafana": {
      "command": "mcp-grafana",
      "env": {
        "GRAFANA_URL": "https://your-stack.grafana.net",
        "GRAFANA_API_KEY": "glsa_..."
      }
    }
  }
}
```

---

## Available Tool Categories

### Dashboard Tools
- `list_dashboards` — List all dashboards with UID and title
- `get_dashboard_by_uid` — Get dashboard JSON by UID
- `search_dashboards` — Full-text search across dashboard titles and tags
- `list_panels` — List panels in a specific dashboard

### Alert Tools
- `list_alerts` — List all alert rules
- `list_alert_groups` — List active alert groups (firing alerts)
- `get_alert_rule_by_uid` — Get specific alert rule definition

### IRM / OnCall Tools
- `list_oncall_teams` — List all teams in Grafana OnCall
- `list_oncall_schedules` — List all on-call schedules
- `get_oncall_schedule` — Get schedule details including current on-call user
- `list_oncall_escalation_chains` — List escalation chains
- `list_oncall_integrations` — List alert integrations

### Incident Tools (Grafana Incident)
- `list_incidents` — List active and recent incidents
- `get_incident` — Get incident details, timeline, and tasks
- `create_incident` — Create a new incident
- `update_incident` — Update incident status, severity, or title
- `add_incident_activity` — Add a timeline event to an incident

### Loki / Log Tools
- `query_loki` — Run a LogQL query against Grafana Loki
- `list_loki_label_names` — List available Loki label names
- `list_loki_label_values` — List values for a specific label

---

## Incident Response Workflows

### Starting an Incident via AI

```
User: "Alert fired: order-service error rate at 4.2%. Start an incident."

AI uses mcp-grafana:
1. create_incident(title="order-service error rate elevated", severity="high")
2. list_dashboards() → find order-service dashboard
3. get_alert_rule_by_uid() → get alert rule details
4. add_incident_activity(incident_id, "Alert details: error rate 4.2%, threshold 1%")
5. get_oncall_schedule(schedule_name="primary") → identify on-call engineer
6. add_incident_activity(incident_id, "On-call: @alice. Notified via IRM escalation.")
```

### Querying Current On-Call

```
User: "Who is on-call right now for the platform team?"

AI uses mcp-grafana:
1. list_oncall_teams() → find platform team ID
2. list_oncall_schedules(team_id=...) → list schedules
3. get_oncall_schedule(schedule_id=...) → shows current shift and user
```

### Correlating Alerts with Logs

```
User: "The order-service alert just fired. Pull the last 10 minutes of error logs."

AI uses mcp-grafana:
1. list_alert_groups() → confirm alert is active
2. query_loki(
     query='{service="order-service", level="error"}',
     start="-10m",
     limit=100
   )
3. Summarize error patterns from log output
```

### Postmortem Timeline Drafting

```
User: "Draft the timeline for incident INC-20260315-001."

AI uses mcp-grafana:
1. get_incident(incident_id="INC-20260315-001") → full incident with activity log
2. list_alert_groups() → correlate with alert timeline
3. Output: structured timeline from incident.created_at through incident.resolved_at
```

---

## Authentication Setup

Grafana IRM requires a **Service Account Token** (not a personal API key):

1. Navigate to: **Grafana → Administration → Service Accounts**
2. Create a service account named `mcp-grafana-agent`
3. Assign roles: `Viewer` (dashboards), `OnCall access` (IRM operations)
4. Generate a token → copy to `GRAFANA_API_KEY`

**Required permissions for IRM operations:**
- `alert.rules:read` — List and get alert rules
- `alert.instances:read` — List firing alerts
- `oncall:read` — List schedules, teams, escalation chains
- `incident:read` — List and get incidents
- `incident:write` — Create and update incidents (optional, for AI-driven incident management)

---

## Example Prompts for AI-Driven Incident Ops

```
"Show me all currently firing critical alerts"
"Who is on-call for the data team right now?"
"Create a SEV1 incident for the auth service outage"
"Query Loki for errors in checkout-service in the last 15 minutes"
"Get the dashboard for order-service and show me the error rate panel"
"List all open incidents and their current status"
"Add a timeline note to incident INC-001: 'Rollback initiated at 14:32 UTC'"
```
