# Better Stack — Terraform Provider Reference

Uses the official `BetterStackHQ/better-uptime` provider.

Provider registry: https://registry.terraform.io/providers/BetterStackHQ/better-uptime/latest
Docs: https://betterstack.com/docs/uptime/terraform/

---

## Provider Setup

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
  api_token = var.better_stack_api_token  # Never hardcode
}
```

---

## Monitors

### HTTP / HTTPS Availability Monitor

```hcl
resource "betterstack_monitor" "api_health" {
  monitor_type    = "status"
  url             = "https://api.example.com/healthz"
  name            = "API — Health Check"
  check_frequency = 60     # Seconds between checks (min: 30)
  regions         = ["us", "eu", "ap"]  # Multi-region checks

  request_timeout          = 15    # seconds
  confirmation_period      = 180   # Wait 3 min before alerting (avoid flap pages)
  recovery_period          = 180   # Wait 3 min after recovery before clearing

  escalation_policy_id = betterstack_escalation_policy.platform_default.id
  email                = true      # Email on alert
  sms                  = false
  call                 = false
  push                 = true      # Mobile push via Better Stack app
}
```

### SSL Certificate Monitor

```hcl
resource "betterstack_monitor" "ssl_api" {
  monitor_type = "ssl"
  url          = "https://api.example.com"
  name         = "API — SSL Certificate"

  # Alert when certificate expires in fewer than this many days
  domain_expiration = 30  # Alert 30 days before expiry

  escalation_policy_id = betterstack_escalation_policy.platform_default.id
}
```

### Keyword Monitor (Response Content Validation)

```hcl
resource "betterstack_monitor" "checkout_healthy" {
  monitor_type    = "keyword"
  url             = "https://checkout.example.com/status"
  name            = "Checkout — Content Validation"
  check_frequency = 120

  # Alert if this keyword is ABSENT from the response body
  required_keyword = "\"status\":\"healthy\""

  escalation_policy_id = betterstack_escalation_policy.platform_default.id
}
```

### Cron Job Heartbeat Monitor

```hcl
resource "betterstack_monitor" "nightly_batch" {
  monitor_type = "cron"
  name         = "Nightly Batch Job"

  # How long to wait for heartbeat before alerting
  expected_cron_period = 86400  # 24 hours in seconds

  escalation_policy_id = betterstack_escalation_policy.platform_default.id
}

output "heartbeat_url" {
  value = betterstack_monitor.nightly_batch.url
  # POST to this URL from your cron job to signal it ran successfully
}
```

### TCP Port Monitor

```hcl
resource "betterstack_monitor" "postgres_port" {
  monitor_type = "tcp"
  url          = "db.example.com"
  port         = 5432
  name         = "PostgreSQL — Port Check"
  check_frequency = 60

  escalation_policy_id = betterstack_escalation_policy.platform_default.id
}
```

---

## Monitor Groups

Group related monitors for organized dashboards and status page components.

```hcl
resource "betterstack_monitor_group" "platform_services" {
  name = "Platform Services"
}

# Associate monitors with the group via monitor_group_id
resource "betterstack_monitor" "order_service" {
  monitor_type     = "status"
  url              = "https://order-service.example.com/healthz"
  name             = "Order Service"
  monitor_group_id = betterstack_monitor_group.platform_services.id
  check_frequency  = 60
  regions          = ["us", "eu"]

  escalation_policy_id = betterstack_escalation_policy.platform_default.id
}
```

---

## On-Call Calendars (Schedules)

```hcl
resource "betterstack_on_call_calendar" "platform_primary" {
  name     = "Platform Primary On-Call"
  timezone = "America/New_York"
}

# Rotations are configured via the Better Stack UI after calendar creation
# or via the API. Terraform manages the calendar container; rotation members
# are set in the dashboard.
```

---

## Escalation Policies

```hcl
resource "betterstack_escalation_policy" "platform_default" {
  name                    = "Platform Team — Default"
  repeat_count            = 2     # Repeat escalation cycle this many times before giving up

  steps {
    type          = "current_on_call"   # Notify current on-call engineer
    wait_before   = 0                   # Notify immediately
  }

  steps {
    type          = "current_on_call"
    calendar_id   = betterstack_on_call_calendar.platform_secondary.id
    wait_before   = 300                 # Wait 5 minutes before escalating to secondary
  }

  steps {
    type          = "all_on_call"       # Notify everyone in the secondary calendar
    wait_before   = 600                 # 10 more minutes
  }
}

resource "betterstack_escalation_policy" "platform_critical" {
  name         = "Platform Team — Critical (Fast Escalation)"
  repeat_count = 3

  steps {
    type        = "current_on_call"
    wait_before = 0
  }

  steps {
    type        = "current_on_call"
    calendar_id = betterstack_on_call_calendar.platform_secondary.id
    wait_before = 120  # 2 minutes — faster for critical
  }

  steps {
    type        = "all_on_call"
    wait_before = 300
  }
}
```

---

## Complete Service Monitor Module

```hcl
# modules/better-stack-service/main.tf
# Usage:
# module "order_service" {
#   source              = "./modules/better-stack-service"
#   service_name        = "order-service"
#   health_check_url    = "https://order-service.example.com/healthz"
#   escalation_policy_id = betterstack_escalation_policy.platform_default.id
#   monitor_group_id    = betterstack_monitor_group.platform.id
# }

variable "service_name"         { type = string }
variable "health_check_url"     { type = string }
variable "escalation_policy_id" { type = string }
variable "monitor_group_id"     { type = string }
variable "check_frequency"      { type = number; default = 60 }
variable "regions"              { type = list(string); default = ["us", "eu"] }

resource "betterstack_monitor" "health" {
  monitor_type     = "status"
  url              = var.health_check_url
  name             = "${var.service_name} — Health"
  check_frequency  = var.check_frequency
  regions          = var.regions
  monitor_group_id = var.monitor_group_id

  confirmation_period = 180
  recovery_period     = 180

  escalation_policy_id = var.escalation_policy_id
}

resource "betterstack_monitor" "ssl" {
  monitor_type      = "ssl"
  url               = var.health_check_url
  name              = "${var.service_name} — SSL"
  domain_expiration = 30
  monitor_group_id  = var.monitor_group_id

  escalation_policy_id = var.escalation_policy_id
}

output "health_monitor_id" {
  value = betterstack_monitor.health.id
}
```
