# Grafana IRM — Terraform Reference

All resources use the `grafana/grafana` provider v3+. IRM resources require the `oncall_access_token` in the provider configuration.

Provider docs: https://registry.terraform.io/providers/grafana/grafana/latest/docs

---

## Provider Configuration

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
  auth = var.grafana_service_account_token  # For dashboards, alerts, etc.

  # IRM (OnCall) operations require a separate access token
  oncall_access_token = var.grafana_oncall_token
}
```

---

## Integration (Alert Ingestion Point)

An integration is the webhook/API endpoint that receives alerts from external sources.

```hcl
resource "grafana_oncall_integration" "alertmanager" {
  name    = "alertmanager-production"
  type    = "alertmanager"  # Options: alertmanager, grafana, pagerduty, webhook, etc.
  team_id = grafana_oncall_team.platform.id

  default_route {
    escalation_chain_id = grafana_oncall_escalation_chain.default.id
  }
}

# After creation, use grafana_oncall_integration.alertmanager.link
# as the webhook URL in your Alertmanager config
output "alertmanager_webhook_url" {
  value = grafana_oncall_integration.alertmanager.link
}
```

**Integration types:**
- `alertmanager` — Prometheus Alertmanager
- `grafana` — Grafana Alerting (native)
- `pagerduty` — Inbound from PagerDuty
- `webhook` — Generic webhook (send any JSON)
- `slack` — Slack slash command
- `email` — Email-based alerts

---

## Route (Alert Routing Rules)

Routes apply grouping and filtering rules on incoming alerts to direct them to escalation chains.

```hcl
resource "grafana_oncall_route" "critical" {
  integration_id      = grafana_oncall_integration.alertmanager.id
  escalation_chain_id = grafana_oncall_escalation_chain.critical.id
  routing_regex       = "severity=critical"
  position            = 0
}

resource "grafana_oncall_route" "warning" {
  integration_id      = grafana_oncall_integration.alertmanager.id
  escalation_chain_id = grafana_oncall_escalation_chain.default.id
  routing_regex       = "severity=warning"
  position            = 1
}
```

---

## Escalation Chain

An escalation chain defines the notification sequence after an alert fires.

```hcl
resource "grafana_oncall_escalation_chain" "default" {
  name    = "platform-team-default"
  team_id = grafana_oncall_team.platform.id
}

# Step 1: Notify on-call primary immediately
resource "grafana_oncall_escalation" "notify_primary" {
  escalation_chain_id = grafana_oncall_escalation_chain.default.id
  type                = "notify_on_call_from_schedule"
  notify_on_call_from_schedule = grafana_oncall_schedule.primary.id
  position            = 0
}

# Step 2: Wait 5 minutes, then escalate
resource "grafana_oncall_escalation" "wait_5min" {
  escalation_chain_id = grafana_oncall_escalation_chain.default.id
  type                = "wait"
  duration            = 300  # seconds
  position            = 1
}

# Step 3: Notify secondary if primary did not acknowledge
resource "grafana_oncall_escalation" "notify_secondary" {
  escalation_chain_id = grafana_oncall_escalation_chain.default.id
  type                = "notify_on_call_from_schedule"
  notify_on_call_from_schedule = grafana_oncall_schedule.secondary.id
  position            = 2
}

# Step 4: Wait 10 more minutes, then notify manager
resource "grafana_oncall_escalation" "wait_10min" {
  escalation_chain_id = grafana_oncall_escalation_chain.default.id
  type                = "wait"
  duration            = 600
  position            = 3
}

resource "grafana_oncall_escalation" "notify_manager" {
  escalation_chain_id = grafana_oncall_escalation_chain.default.id
  type                = "notify_persons"
  persons_to_notify   = [data.grafana_oncall_user.manager.id]
  position            = 4
}
```

**Escalation step types:**
- `notify_on_call_from_schedule` — Notify whoever is on-call in the referenced schedule
- `notify_persons` — Notify specific named users
- `notify_persons_next_each_time` — Round-robin through a list
- `wait` — Pause before proceeding (duration in seconds)
- `trigger_webhook` — Call an external webhook
- `resolve` — Auto-resolve after escalation completes

---

## Schedule (On-Call Rotations)

```hcl
resource "grafana_oncall_schedule" "primary" {
  name      = "platform-primary"
  type      = "rolling_users"
  team_id   = grafana_oncall_team.platform.id
  time_zone = "America/New_York"

  rolling_users = [
    [data.grafana_oncall_user.alice.id],
    [data.grafana_oncall_user.bob.id],
    [data.grafana_oncall_user.charlie.id],
    [data.grafana_oncall_user.diana.id],
  ]

  shifts = [grafana_oncall_on_call_shift.weekly.id]
}

resource "grafana_oncall_on_call_shift" "weekly" {
  name      = "weekly-shift"
  type      = "rolling_users"
  team_id   = grafana_oncall_team.platform.id
  start     = "2026-01-06T09:00:00"  # First Monday of deployment
  duration  = 604800                  # 7 days in seconds
  frequency = "weekly"
  time_zone = "America/New_York"
}
```

### PTO Override

```hcl
resource "grafana_oncall_on_call_shift" "pto_override" {
  name      = "alice-pto-2026-03"
  type      = "override"
  team_id   = grafana_oncall_team.platform.id
  start     = "2026-03-10T09:00:00"
  duration  = 604800  # 1 week
  time_zone = "America/New_York"

  rolling_users = [[data.grafana_oncall_user.bob.id]]  # Bob covers Alice's week
}
```

---

## User and Team Lookups

```hcl
data "grafana_oncall_user" "alice" {
  username = "alice@example.com"
}

data "grafana_oncall_team" "platform" {
  name = "platform"
}

resource "grafana_oncall_team" "platform" {
  name = "platform"
}
```

---

## Slack ChatOps Integration

```hcl
resource "grafana_oncall_integration" "slack_commands" {
  name    = "slack-oncall"
  type    = "slack"
  team_id = grafana_oncall_team.platform.id

  default_route {
    escalation_chain_id = grafana_oncall_escalation_chain.default.id
    slack {
      channel_id            = var.slack_incidents_channel_id
      enabled               = true
    }
  }
}
```

---

## Complete Module Pattern

```hcl
# modules/grafana-irm-service/main.tf
# Reusable module for per-service IRM setup
variable "service_name"        { type = string }
variable "team_id"             { type = string }
variable "primary_schedule_id" { type = string }
variable "secondary_schedule_id" { type = string }
variable "slack_channel_id"    { type = string }

resource "grafana_oncall_escalation_chain" "service" {
  name    = "${var.service_name}-escalation"
  team_id = var.team_id
}

resource "grafana_oncall_escalation" "primary" {
  escalation_chain_id          = grafana_oncall_escalation_chain.service.id
  type                         = "notify_on_call_from_schedule"
  notify_on_call_from_schedule = var.primary_schedule_id
  position                     = 0
}

resource "grafana_oncall_escalation" "wait" {
  escalation_chain_id = grafana_oncall_escalation_chain.service.id
  type                = "wait"
  duration            = 300
  position            = 1
}

resource "grafana_oncall_escalation" "secondary" {
  escalation_chain_id          = grafana_oncall_escalation_chain.service.id
  type                         = "notify_on_call_from_schedule"
  notify_on_call_from_schedule = var.secondary_schedule_id
  position                     = 2
}

resource "grafana_oncall_integration" "service" {
  name    = "${var.service_name}-alertmanager"
  type    = "alertmanager"
  team_id = var.team_id

  default_route {
    escalation_chain_id = grafana_oncall_escalation_chain.service.id
    slack {
      channel_id = var.slack_channel_id
      enabled    = true
    }
  }
}

output "webhook_url" {
  value = grafana_oncall_integration.service.link
}
```
