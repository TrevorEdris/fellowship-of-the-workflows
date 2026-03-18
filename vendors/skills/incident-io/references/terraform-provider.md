# incident.io — Terraform Provider Reference

Uses the official `incident-io/incident` provider. Current stable version: v5+.

Provider registry: https://registry.terraform.io/providers/incident-io/incident/latest
GitHub: https://github.com/incident-io/terraform-provider-incident

---

## Provider Setup

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
  api_key = var.incident_io_api_key  # Never hardcode; use var or secret manager
}
```

---

## Severity Levels

```hcl
resource "incident_severity" "critical" {
  name        = "Critical"
  description = "Total service failure. All users affected."
  rank        = 1  # Lower rank = higher severity
}

resource "incident_severity" "high" {
  name        = "High"
  description = "Significant degradation. Majority of users affected."
  rank        = 2
}

resource "incident_severity" "medium" {
  name        = "Medium"
  description = "Partial failure. Subset of users or features affected."
  rank        = 3
}

resource "incident_severity" "low" {
  name        = "Low"
  description = "Minor anomaly. No current user impact."
  rank        = 4
}
```

---

## Incident Types

```hcl
resource "incident_type" "service_outage" {
  name                    = "Service Outage"
  description             = "A service is down or severely degraded"
  create_in_triage_mode   = false  # Skip triage, go straight to active
  private_incidents_only  = false
}

resource "incident_type" "security_incident" {
  name                    = "Security Incident"
  description             = "Security breach, data exposure, or unauthorized access"
  create_in_triage_mode   = false
  private_incidents_only  = true   # Security incidents are private by default
}

resource "incident_type" "customer_impacting" {
  name                    = "Customer Impacting"
  description             = "Customer-reported or user-visible degradation"
  create_in_triage_mode   = true   # Start in triage, confirm before escalating
  private_incidents_only  = false
}
```

---

## Incident Roles

```hcl
resource "incident_role" "incident_lead" {
  name                        = "Incident Lead"
  description                 = "Owns the incident response. Coordinates communication and resolution."
  shortform                   = "lead"
  required                    = true
  instructions                = "You are responsible for driving the incident to resolution. Delegate investigation, coordinate communication, and run the postmortem."
}

resource "incident_role" "communications" {
  name         = "Communications"
  description  = "Manages external and internal stakeholder communications."
  shortform    = "comms"
  required     = false
  instructions = "Update the status page, post to #incidents-updates, and brief executive stakeholders for SEV0/1."
}

resource "incident_role" "subject_matter_expert" {
  name         = "Subject Matter Expert"
  description  = "Provides deep technical context for the affected system."
  shortform    = "sme"
  required     = false
  instructions = "Assist the Incident Lead with root cause investigation. You do not need to drive the incident."
}
```

---

## On-Call Schedules

```hcl
resource "incident_schedule" "platform_primary" {
  name         = "Platform Primary On-Call"
  timezone     = "America/New_York"

  rotations = [
    {
      name            = "weekly-rotation"
      handover_start_at = "2026-01-05T09:00:00Z"
      handover_interval_days = 7
      users = [
        { id = data.incident_user.alice.id },
        { id = data.incident_user.bob.id },
        { id = data.incident_user.charlie.id },
        { id = data.incident_user.diana.id },
      ]
      layers = [
        {
          name = "Primary"
          users = [
            { id = data.incident_user.alice.id },
            { id = data.incident_user.bob.id },
            { id = data.incident_user.charlie.id },
            { id = data.incident_user.diana.id },
          ]
        }
      ]
    }
  ]
}
```

---

## Escalation Policies

```hcl
resource "incident_escalation_policy" "platform_default" {
  name    = "Platform Team — Default"
  team_id = data.incident_team.platform.id

  steps = [
    {
      delay_minutes = 0
      targets = [
        {
          type       = "schedule"
          schedule   = { id = incident_schedule.platform_primary.id }
          urgency    = "high"
        }
      ]
    },
    {
      delay_minutes = 5
      targets = [
        {
          type       = "schedule"
          schedule   = { id = incident_schedule.platform_secondary.id }
          urgency    = "high"
        }
      ]
    },
    {
      delay_minutes = 15
      targets = [
        {
          type = "user"
          user = { id = data.incident_user.manager.id }
          urgency = "high"
        }
      ]
    }
  ]
}
```

---

## Catalog Types and Entries

The Catalog models your service ownership graph. Each entry maps a service to its team, runbook, and escalation policy.

```hcl
resource "incident_catalog_type" "service" {
  name        = "Service"
  description = "Engineering services and their ownership metadata"

  schema = {
    attributes = [
      { id = "team",             name = "Team",              type = "CatalogEntry[Team]",              required = true },
      { id = "runbook_url",      name = "Runbook URL",       type = "String",                           required = false },
      { id = "escalation_policy",name = "Escalation Policy", type = "CatalogEntry[EscalationPolicy]",  required = false },
      { id = "slack_channel",    name = "Slack Channel",     type = "String",                           required = false },
    ]
  }
}

resource "incident_catalog_entry" "order_service" {
  catalog_type_id = incident_catalog_type.service.id
  name            = "order-service"

  attribute_values = {
    team             = { catalog_entry = { id = incident_catalog_entry.platform_team.id } }
    runbook_url      = { value = "https://wiki.example.com/runbooks/order-service" }
    slack_channel    = { value = "#platform-incidents" }
  }
}
```

---

## Workflows

```hcl
resource "incident_workflow" "auto_create_slack_channel" {
  name    = "Auto-create Slack channel on incident declaration"
  trigger = "incident.declared"
  enabled = true

  steps = [
    {
      for_each = null
      id       = "create-channel"
      name     = "Create Slack channel"
      action   = "incident.create_slack_channel"
      param_bindings = [
        {
          name  = "channel_name_prefix"
          value = { literal = "inc" }
        }
      ]
    }
  ]
}

resource "incident_workflow" "auto_assign_lead" {
  name    = "Auto-assign incident lead from on-call"
  trigger = "incident.declared"
  enabled = true

  steps = [
    {
      for_each = null
      id       = "assign-lead"
      name     = "Assign incident lead"
      action   = "incident.assign_role"
      param_bindings = [
        {
          name  = "role"
          value = { literal = incident_role.incident_lead.id }
        },
        {
          name  = "user_from_schedule"
          value = { literal = incident_schedule.platform_primary.id }
        }
      ]
    }
  ]
}
```

---

## Data Sources

```hcl
data "incident_user" "alice" {
  email = "alice@example.com"
}

data "incident_team" "platform" {
  name = "Platform"
}
```
