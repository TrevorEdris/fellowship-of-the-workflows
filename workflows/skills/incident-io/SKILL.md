---
name: incident-io
description: incident.io specialist. Configures incident.io for Slack-native incident response, alert routing, automation workflows, and structured postmortems. Includes Terraform (official provider v5+) and MCP server integration. Best fit for modern SRE shops and teams migrating from OpsGenie.
context: fork
agent: incident-io-specialist
allowed-tools: Bash, Glob, Grep, Read, WebFetch
---

# incident.io

incident.io specialist. incident.io is a Slack-native incident management platform with structured workflows, a catalog system, and an official MCP server with native Claude support. The fastest-growing platform in the 50–500 engineer segment.

## When to Use

- Configuring incident.io for a team or service
- Setting up alert routing and on-call schedules via incident.io
- Automating incident workflows (auto-assign, auto-escalate, status updates)
- Managing incident.io infrastructure as code with Terraform
- Using the incident.io MCP server for AI-assisted incident operations
- Migrating from OpsGenie (EOL April 2027) to a modern platform

## Platform Context

**Best fit for:** Slack-native teams, modern SRE shops, companies where incident response is Slack-first. Time-to-operational is 3–5 days vs. PagerDuty's 2–6 weeks per industry data.

**MCP status:** Official MCP server, Claude-native, remote (no local install required). This is one of the strongest MCP implementations in the incident management space.

**Pricing:** ~$16/responder/month. Responders = engineers who actively respond to incidents (not viewers).

## Modes

### `setup`

Configure incident.io from scratch. Gather:
1. incident.io organization slug (from app.incident.io URL)
2. API key (Settings → API keys → Create key)
3. Slack workspace connection (done via UI; required before Terraform)
4. Team structure and initial severities

Steps:
1. Connect Slack workspace: **Settings → Integrations → Slack**
2. Install incident.io Slack app to your workspace
3. Create your first severity levels and incident types via UI
4. Generate API key: **Settings → API keys → New API key** (scopes: read + write)
5. Initialize Terraform (see `references/terraform-provider.md`)

### `workflows`

Configure automation workflows — rules that trigger actions based on incident events. See `references/workflows.md`.

Common workflows:
- Auto-create a Slack channel when an incident is declared
- Auto-assign on-call engineer as incident lead
- Auto-post status updates to a status channel at severity thresholds
- Auto-escalate if incident is open > 30 minutes without update

### `catalog`

Use the incident.io Catalog to model your service ownership, team structure, and runbook relationships. The Catalog powers intelligent routing and context injection in incident workflows.

Key catalog types:
- `Service` — links service name → owning team → runbook URL → escalation policy
- `Team` — maps team name → members → on-call schedule
- `Feature` — links product features to owning services

### `terraform`

Manage incident.io configuration as code. See `references/terraform-provider.md` for complete resource examples including:
- `incident_severity`
- `incident_type`
- `incident_role`
- `incident_workflow`
- `incident_catalog_type`
- `incident_catalog_entry`
- `incident_schedule`
- `incident_escalation_policy`

### `mcp`

Use the incident.io MCP server for AI-driven incident operations. See `references/mcp-usage.md` for:
- Listing and creating incidents
- Querying incident timelines and activity
- Triggering escalations and workflow actions
- Drafting postmortems from incident data

## Quick Start (Terraform)

```hcl
terraform {
  required_providers {
    incident = {
      source  = "incident-io/incident"
      version = "~> 5.0"
    }
  }
}

provider "incident" {
  api_key = var.incident_io_api_key
}

# Basic severity levels
resource "incident_severity" "critical" {
  name        = "Critical"
  description = "All users affected; complete service failure"
  rank        = 1
}

resource "incident_severity" "high" {
  name        = "High"
  description = "Majority of users affected; significant degradation"
  rank        = 2
}
```

## Migration from OpsGenie

OpsGenie shuts down April 5, 2027. Migration steps:

1. Export OpsGenie teams and schedules via API
2. Map OpsGenie escalation policies → incident.io escalation policies
3. Recreate on-call schedules in incident.io (UI or Terraform)
4. Update alert sources: replace OpsGenie webhook URLs with incident.io alert source URLs
5. Migrate runbook links (update URLs in incident.io catalog entries)
6. Run 2-week parallel operation before decommissioning OpsGenie
7. Cancel OpsGenie subscription before June 2027 (billing continues until cancellation even after shutdown)

## References

- `references/terraform-provider.md` — Complete Terraform resource examples for the incident.io provider
- `references/workflows.md` — Automation workflow patterns and trigger/action catalog
- `references/mcp-usage.md` — MCP server capabilities and incident workflow examples
