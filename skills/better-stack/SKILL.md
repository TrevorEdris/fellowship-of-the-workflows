---
name: better-stack
description: Better Stack specialist. Configures Better Stack's unified monitoring, alerting, on-call scheduling, and status pages. Includes Terraform (BetterStackHQ/better-uptime provider) and MCP server usage. Best fit for startups and mid-market teams wanting consolidated uptime monitoring + log aggregation + alerting + status pages at lower cost than Datadog + PagerDuty.
context: fork
agent: better-stack-specialist
allowed-tools: Bash, Glob, Grep, Read, WebFetch
tags: [observability, incident-response]
---

# Better Stack

Better Stack specialist. Better Stack consolidates uptime monitoring, log aggregation, alerting, on-call scheduling, and branded status pages into a single platform. The strongest value proposition for teams wanting to reduce vendor count.

## When to Use

- Consolidating uptime monitoring + alerting + on-call + status pages into one platform
- Configuring Better Stack monitors and on-call policies via Terraform
- Setting up branded status pages with subscriber management
- Using the Better Stack MCP server for AI-assisted incident operations
- Teams evaluating alternatives to Datadog + PagerDuty as a cost-reduction strategy
- Startups and mid-market companies (up to ~500 engineers) looking for developer-friendly tooling

## Platform Context

**Unique value:** Better Stack bundles five separate products that most teams purchase independently:
1. Uptime monitoring (HTTP, TCP, keyword, SSL, DNS, cron)
2. Log aggregation + search (Loki-compatible API)
3. Alerting and on-call scheduling
4. Status pages (branded, custom domain, custom CSS, subscriber email/SMS)
5. AI-assisted postmortem drafting

**Best fit for:** Startups and mid-market companies. Strong adoption in companies that currently use Pingdom + PagerDuty + Statuspage.io + a log aggregator as separate tools.

**MCP status:** Official MCP server announced in Changelog #12. Covers incidents, on-call, log queries, and postmortem drafting.

**Pricing:** Free tier available (limited monitors). Paid tiers based on monitor count and user seats.

## Modes

### `monitor`

Configure uptime monitors and alerting rules. See `references/monitors-and-alerting.md`.

Monitor types:
- `status` — HTTP/HTTPS availability check (2xx = up, other = down)
- `expected_status_codes` — Check for specific HTTP status codes
- `keyword` — Confirm a keyword appears/does not appear in response body
- `keyword_absence` — Confirm a keyword is absent
- `ping` — ICMP ping
- `tcp` — TCP port check
- `dns` — DNS resolution check
- `ssl` — SSL certificate expiry check
- `cron` — Cron job heartbeat (alert if job does not check in)

### `on-call`

Configure on-call schedules and escalation policies. See `references/monitors-and-alerting.md` for policy examples.

### `status-page`

Configure branded status pages with subscriber management, custom domains, and component grouping. See `references/status-pages.md`.

### `terraform`

Manage Better Stack configuration as code. See `references/terraform-provider.md` for complete resource examples including:
- `betterstack_monitor`
- `betterstack_monitor_group`
- `betterstack_on_call_calendar`
- `betterstack_escalation_policy`
- `betterstack_status_page`
- `betterstack_status_page_section`
- `betterstack_status_page_resource`

### `mcp`

Use the Better Stack MCP server for AI-driven operations. See `references/mcp-usage.md` (within monitors-and-alerting.md).

## Quick Start (Terraform)

```hcl
terraform {
  required_providers {
    betterstack = {
      source  = "BetterStackHQ/better-uptime"
      version = "~> 0.6"
    }
  }
}

provider "betterstack" {
  api_token = var.better_stack_api_token
}

# Basic HTTP monitor
resource "betterstack_monitor" "api_health" {
  monitor_type = "status"
  url          = "https://api.example.com/healthz"
  name         = "API Health Check"
  check_frequency = 60  # seconds
  regions = ["us", "eu", "ap"]

  escalation_policy_id = betterstack_escalation_policy.default.id
}
```

## References

- `references/terraform-provider.md` — Complete Terraform resource examples
- `references/monitors-and-alerting.md` — Monitor types, on-call policies, MCP usage
- `references/status-pages.md` — Status page configuration and subscriber management
