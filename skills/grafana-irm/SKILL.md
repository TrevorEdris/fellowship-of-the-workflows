---
name: grafana-irm
description: Grafana Cloud IRM specialist. Configures Grafana IRM (formerly OnCall + Grafana Incident) for alert routing, on-call scheduling, escalation chains, and incident response. Includes Terraform (grafana_oncall_* resources) and MCP (mcp-grafana) usage. Use for teams on the Grafana + Prometheus + OTel stack.
context: fork
agent: grafana-irm-specialist
allowed-tools: Bash, Glob, Grep, Read, WebFetch
---

# Grafana IRM

Grafana Cloud IRM specialist. Grafana IRM merges Grafana OnCall (on-call scheduling, escalation) and Grafana Incident (incident management, postmortem) into a single product. This skill covers setup, Terraform automation, and MCP-driven workflows.

## When to Use

- Configuring on-call schedules and escalation chains on Grafana Cloud
- Setting up alert routing from Grafana Alerting or external sources to on-call
- Managing Grafana IRM infrastructure as code with Terraform
- Using the `mcp-grafana` MCP server for AI-assisted incident operations
- Migrating from Grafana OnCall OSS (archived March 2026) to Grafana Cloud IRM

## Platform Context

**Important status:** Grafana OnCall OSS entered maintenance mode March 2025 and will be archived March 2026. All users should migrate to Grafana Cloud IRM. The `grafana/mcp-grafana` MCP server covers both Grafana dashboards and IRM operations.

**Best fit for:** Teams already on Grafana Cloud with OTel/Prometheus metric pipelines. Grafana Alerting → IRM is a zero-new-vendor path.

## Modes

### `setup`

Configure Grafana IRM from scratch. Gather:
1. Grafana Cloud stack URL and API key
2. Team structure (number of engineers, timezone distribution)
3. Alert sources (Grafana Alerting, PagerDuty webhook, Prometheus Alertmanager, or external)
4. Slack workspace ID (for ChatOps integration)

Steps:
1. Enable IRM on your Grafana Cloud stack (via Grafana Cloud Portal → IRM tab)
2. Install the Grafana OnCall Slack app in your workspace
3. Create integration: `Settings → Integrations → Add Integration`
4. Configure escalation chain (see `references/alert-routing.md`)
5. Set up on-call schedule (see `references/terraform-irm.md`)

### `escalation-chain`

Design and configure escalation chains. Chains define the sequence of notifications when an alert fires. See `references/alert-routing.md` for patterns.

### `schedule`

Set up on-call rotation schedules. Grafana IRM supports:
- Simple shifts (one engineer for a duration)
- Rolling rotations (round-robin across a team)
- Custom rotations (complex handoff patterns)
- Overrides (PTO coverage, manual swaps)

### `terraform`

Manage Grafana IRM via Terraform. See `references/terraform-irm.md` for complete resource examples including:
- `grafana_oncall_escalation_chain`
- `grafana_oncall_escalation`
- `grafana_oncall_schedule`
- `grafana_oncall_on_call_shift`
- `grafana_oncall_integration`
- `grafana_oncall_route`

### `mcp`

Use the `mcp-grafana` MCP server for AI-driven incident operations. See `references/mcp-usage.md` for:
- Listing active alerts and incidents
- Querying dashboards and panel data
- Triggering escalations
- Drafting incident timelines

## Quick Start (Terraform)

```hcl
terraform {
  required_providers {
    grafana = {
      source  = "grafana/grafana"
      version = "~> 3.0"
    }
  }
}

provider "grafana" {
  url  = var.grafana_url
  auth = var.grafana_service_account_token
}

# Import for IRM-specific resources
provider "grafana" {
  alias                     = "oncall"
  url                       = var.grafana_url
  oncall_access_token       = var.grafana_oncall_token
}
```

## Migration from OnCall OSS

If migrating from self-hosted Grafana OnCall (OSS):
1. Export existing schedules via OnCall API: `GET /api/v1/schedules`
2. Export escalation chains: `GET /api/v1/escalation_chains`
3. Create a Grafana Cloud account and enable IRM
4. Recreate via Terraform using `grafana_oncall_*` resources (same resource schema)
5. Update alert source webhook URLs to new Cloud IRM endpoints
6. Decommission OSS instance after 2-week parallel run

## References

- `references/terraform-irm.md` — Complete Terraform resource examples for grafana_oncall_* resources
- `references/alert-routing.md` — Integration setup, escalation chain patterns, route configuration
- `references/mcp-usage.md` — mcp-grafana tool catalog and incident workflow examples
