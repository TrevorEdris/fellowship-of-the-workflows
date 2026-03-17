terraform {
  required_providers {
    pagerduty = {
      source  = "PagerDuty/pagerduty"
      version = "~> 3.0"
    }
  }
}

locals {
  auto_resolve_timeout_map = {
    critical = null   # No auto-resolve for critical services
    high     = 14400  # 4 hours
    medium   = 7200   # 2 hours
    low      = 3600   # 1 hour
  }

  acknowledgement_timeout_map = {
    critical = null  # No auto-acknowledge
    high     = 1800  # 30 minutes
    medium   = 600   # 10 minutes
    low      = 300   # 5 minutes
  }
}

# PagerDuty Service
resource "pagerduty_service" "this" {
  name                    = var.service_name
  description             = var.description
  escalation_policy       = var.escalation_policy_id
  auto_resolve_timeout    = local.auto_resolve_timeout_map[var.criticality_tier]
  acknowledgement_timeout = local.acknowledgement_timeout_map[var.criticality_tier]
  alert_creation          = "create_alerts_and_incidents"

  alert_grouping_parameters {
    type = "time"
    config {
      timeout = var.alert_grouping_timeout_seconds
    }
  }
}

# Datadog Integration
resource "pagerduty_service_integration" "datadog" {
  count   = var.create_datadog_integration ? 1 : 0
  name    = "Datadog"
  service = pagerduty_service.this.id
  vendor  = data.pagerduty_vendor.datadog[0].id
}

data "pagerduty_vendor" "datadog" {
  count = var.create_datadog_integration ? 1 : 0
  name  = "Datadog"
}

# AlertManager / Generic Events API v2 Integration
resource "pagerduty_service_integration" "events_api" {
  count   = var.create_events_api_integration ? 1 : 0
  name    = coalesce(var.events_api_integration_name, "${var.service_name}-events-api")
  service = pagerduty_service.this.id
  type    = "events_api_v2_inbound_integration"
}

# Service Dependency (optional)
resource "pagerduty_service_dependency" "upstream" {
  for_each = toset(var.upstream_service_ids)

  dependency {
    dependent_service {
      id   = pagerduty_service.this.id
      type = "service"
    }
    supporting_service {
      id   = each.value
      type = "service"
    }
  }
}
