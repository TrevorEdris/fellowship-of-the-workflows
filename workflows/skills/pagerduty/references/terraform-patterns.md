# PagerDuty Terraform Patterns

Provider: `hashicorp/pagerduty` v3.x

---

## Provider Configuration

```hcl
terraform {
  required_providers {
    pagerduty = {
      source  = "PagerDuty/pagerduty"
      version = "~> 3.0"
    }
  }
}

provider "pagerduty" {
  token = var.pagerduty_token  # Never hardcode — use var + secrets manager
}
```

---

## Core Resources

### `pagerduty_service`

```hcl
resource "pagerduty_service" "example" {
  name                    = "payments-service"
  description             = "Handles payment processing for all channels"
  escalation_policy       = pagerduty_escalation_policy.payments.id
  auto_resolve_timeout    = 14400   # seconds; null = disabled
  acknowledgement_timeout = 1800    # seconds; null = disabled
  alert_creation          = "create_alerts_and_incidents"

  alert_grouping_parameters {
    type = "time"
    config {
      timeout = 300  # 5 minutes
    }
  }
}
```

### `pagerduty_service_integration`

Creates an integration key (routing_key) for a specific monitoring tool:

```hcl
# Datadog integration
resource "pagerduty_service_integration" "payments_datadog" {
  name    = "Datadog"
  service = pagerduty_service.payments.id
  vendor  = data.pagerduty_vendor.datadog.id
}

data "pagerduty_vendor" "datadog" {
  name = "Datadog"
}

# AlertManager (Prometheus) integration — use generic Events API v2
resource "pagerduty_service_integration" "payments_alertmanager" {
  name    = "AlertManager"
  service = pagerduty_service.payments.id
  type    = "events_api_v2_inbound_integration"
}

output "payments_alertmanager_integration_key" {
  value     = pagerduty_service_integration.payments_alertmanager.integration_key
  sensitive = true
}
```

### `pagerduty_event_orchestration`

```hcl
resource "pagerduty_event_orchestration" "global" {
  name = "global-routing"
}

resource "pagerduty_event_orchestration_global" "routing_rules" {
  event_orchestration = pagerduty_event_orchestration.global.id

  set {
    id = "start"

    rule {
      label = "Route payments to payments service"
      condition {
        expression = "event.custom_details.service matches 'payments*'"
      }
      actions {
        route_to = pagerduty_event_orchestration_service.payments.id
      }
    }

    rule {
      label = "Suppress info-level events"
      condition {
        expression = "event.severity matches 'info'"
      }
      actions {
        suppress = true
      }
    }
  }

  catch_all {
    actions {
      route_to = "unrouted"
    }
  }
}
```

### `pagerduty_maintenance_window`

```hcl
resource "pagerduty_maintenance_window" "deploy_window" {
  start_time  = "2025-03-01T02:00:00-05:00"
  end_time    = "2025-03-01T04:00:00-05:00"
  description = "Scheduled deployment maintenance"

  services = [pagerduty_service.payments.id]
}
```

---

## Reusable Module Pattern

The recommended pattern is a module that accepts service parameters and outputs the `integration_key`. This key is the contract between PD Terraform and your observability Terraform.

### Module Interface

```
modules/pagerduty-service/
├── main.tf        # Resources
├── variables.tf   # Inputs
└── outputs.tf     # integration_key output
```

### Consumption Pattern

```hcl
module "payments_pagerduty" {
  source = "./modules/pagerduty-service"

  service_name         = "payments-service"
  team                 = "payments"
  escalation_policy_id = pagerduty_escalation_policy.payments.id
  runbook_url          = "https://wiki.internal/runbooks/payments"
  criticality_tier     = "high"  # critical | high | medium | low
}

# Feed integration_key into Datadog Terraform
module "payments_datadog_monitor" {
  source = "./modules/datadog-monitor"

  service_name    = "payments-service"
  pagerduty_key   = module.payments_pagerduty.integration_key
}

# Feed integration_key into AlertManager config
resource "kubernetes_secret" "alertmanager_pd_key" {
  data = {
    pagerduty_integration_key = module.payments_pagerduty.integration_key
  }
}
```

See `assets/terraform-module/` for the complete module files.

---

## Importing Existing Resources

Organizations frequently have PD resources created through the UI. Always import before planning new resources.

### Finding Resource IDs

Service ID: visible in the PD UI URL when viewing a service — `https://yourorg.pagerduty.com/services/P1AB2CD`

Escalation policy ID: visible in URL when viewing policy — `https://yourorg.pagerduty.com/escalation_policies/P3EF4GH`

Schedule ID: `https://yourorg.pagerduty.com/schedules/P5IJ6KL`

### Import Commands

```bash
# Import a service
terraform import pagerduty_service.payments P1AB2CD

# Import an escalation policy
terraform import pagerduty_escalation_policy.team_payments P3EF4GH

# Import a schedule
terraform import pagerduty_schedule.payments_primary P5IJ6KL

# Import a service integration
# Format: <service_id>:<integration_id>
terraform import pagerduty_service_integration.payments_datadog P1AB2CD:P7MN8OP
```

### Import Workflow

1. Run `terraform plan` — identify resources that exist in PD but not in state.
2. Look up each resource ID in the PD UI or via API.
3. Write the Terraform resource block (without creating it).
4. Run `terraform import` for each resource.
5. Run `terraform plan` again — should show no changes for imported resources.
6. If `plan` shows drift, update HCL to match actual configuration.

---

## Conventions

- One Terraform workspace per environment (`prod`, `staging`) — PD services are typically shared, but integration keys differ by environment.
- Store `pagerduty_token` in Vault or as a CI/CD secret, never in `.tfvars` committed to git.
- Tag all resources with `team` and `env` using `pagerduty_tag` resources for cost and ownership attribution.
- Pin provider version to minor release (`~> 3.0`) to get patches without breaking changes.
