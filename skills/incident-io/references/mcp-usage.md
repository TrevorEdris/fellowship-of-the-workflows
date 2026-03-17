# incident.io — MCP Usage Reference

The incident.io MCP server is an official, Claude-native remote MCP server. No local installation required — connect via remote URL with your API key.

**Announcement:** https://incident.io/changelog/introducing-incident-io-mcp
**Type:** Remote MCP server (HTTPS)
**Compatibility:** Claude Desktop, Claude Code, Cursor, and any MCP-compatible client

---

## Connection Setup

### Claude Desktop

```json
// ~/Library/Application Support/Claude/claude_desktop_config.json
{
  "mcpServers": {
    "incident-io": {
      "url": "https://api.incident.io/mcp",
      "headers": {
        "Authorization": "Bearer YOUR_INCIDENT_IO_API_KEY"
      }
    }
  }
}
```

### Claude Code (claude.ai/code)

In your project's MCP settings or `.claude/mcp.json`:

```json
{
  "mcpServers": {
    "incident-io": {
      "url": "https://api.incident.io/mcp",
      "headers": {
        "Authorization": "Bearer YOUR_INCIDENT_IO_API_KEY"
      }
    }
  }
}
```

### Cursor

```json
// .cursor/mcp.json
{
  "mcpServers": {
    "incident-io": {
      "url": "https://api.incident.io/mcp",
      "headers": {
        "Authorization": "Bearer ${INCIDENT_IO_API_KEY}"
      }
    }
  }
}
```

**API Key scopes required:** `incidents:read`, `incidents:write`, `catalog:read`, `schedules:read`

---

## Available Tools

### Incident Lifecycle
- `list_incidents` — List incidents with filters (status, severity, date range)
- `get_incident` — Get full incident details including timeline and roles
- `create_incident` — Declare a new incident
- `update_incident` — Update severity, status, title, or custom fields
- `resolve_incident` — Mark incident as resolved

### Timeline and Activity
- `add_incident_update` — Add a status update to an incident
- `list_incident_updates` — List all timeline updates for an incident
- `add_incident_action` — Create a follow-up action item

### Roles and Assignments
- `assign_incident_role` — Assign a role (lead, comms, SME) to a user
- `list_incident_roles` — List configured roles

### Catalog
- `search_catalog` — Search catalog entries by name, type, or attributes
- `get_catalog_entry` — Get a specific catalog entry (e.g., a service's runbook URL)
- `list_catalog_types` — List all catalog type definitions

### On-Call and Schedules
- `list_schedules` — List all on-call schedules
- `get_who_is_on_call` — Get the current on-call engineer for a schedule
- `list_escalation_policies` — List configured escalation policies

---

## AI-Driven Incident Workflows

### Declaring an Incident from an Alert

```
User: "order-service error rate hit 4.2%. Declare an incident."

AI uses incident.io MCP:
1. create_incident(
     title="order-service error rate elevated",
     severity="high",
     incident_type="Service Outage"
   )
2. get_who_is_on_call(schedule="platform-primary")
   → returns: @alice
3. assign_incident_role(
     incident_id=INC-123,
     role="Incident Lead",
     user_email="alice@example.com"
   )
4. search_catalog(type="Service", name="order-service")
   → returns runbook URL: https://wiki.example.com/runbooks/order-service
5. add_incident_update(
     incident_id=INC-123,
     message="Alert: error rate 4.2%, threshold 1%. Runbook: {url}. @alice assigned as lead."
   )
```

### Checking Current On-Call

```
User: "Who's on-call for the data team right now?"

AI uses incident.io MCP:
1. list_schedules() → filter for data team schedules
2. get_who_is_on_call(schedule_id="sched_data_primary")
   → returns: @bob (current), @charlie (backup)
```

### Searching for a Service's Runbook

```
User: "What's the runbook for the payment-service?"

AI uses incident.io MCP:
1. search_catalog(type="Service", name="payment-service")
   → returns entry with runbook_url attribute
2. Output: "Runbook: https://wiki.example.com/runbooks/payment-service"
```

### Postmortem Preparation

```
User: "Help me write the postmortem for incident INC-456."

AI uses incident.io MCP:
1. get_incident(incident_id="INC-456")
   → title, severity, start/end times, impact description
2. list_incident_updates(incident_id="INC-456")
   → full chronological timeline of updates
3. list_incident_actions(incident_id="INC-456")
   → follow-up action items created during incident
4. AI drafts postmortem from postmortem template with the above data pre-filled
```

### Incident Status Check

```
User: "What are our open SEV0 and SEV1 incidents?"

AI uses incident.io MCP:
1. list_incidents(
     status=["active", "triage"],
     severity=["critical", "high"]
   )
2. For each incident: title, duration open, assigned lead, last update
3. Summary: "2 active incidents: INC-123 (SEV1, order-service, 45m open, lead: @alice) ..."
```

---

## Example Natural Language Prompts

```
"Declare a critical incident: payment gateway is down for all EU users"
"Who is on-call right now for the platform team?"
"What is the runbook for checkout-service?"
"List all open incidents and their current owners"
"Add a timeline update to INC-789: 'Root cause confirmed — DB connection pool exhausted'"
"Mark incident INC-789 as resolved"
"Create a follow-up action: 'Increase DB connection pool limit' assigned to @bob, due 2026-03-20"
"Help me draft the postmortem for last week's SEV1 incident"
```
