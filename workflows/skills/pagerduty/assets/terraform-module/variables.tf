variable "service_name" {
  type        = string
  description = "Name of the PagerDuty service. Should match the logical service name used in your observability stack."

  validation {
    condition     = can(regex("^[a-z][a-z0-9-]*$", var.service_name))
    error_message = "service_name must be lowercase alphanumeric with hyphens, starting with a letter."
  }
}

variable "description" {
  type        = string
  description = "Human-readable description of this PagerDuty service."
  default     = ""
}

variable "team" {
  type        = string
  description = "Owning team name. Used for tagging and naming conventions."
}

variable "escalation_policy_id" {
  type        = string
  description = "ID of the PagerDuty escalation policy to attach to this service."
}

variable "runbook_url" {
  type        = string
  description = "URL to the runbook for incidents on this service. Included in incident details."
  default     = ""
}

variable "criticality_tier" {
  type        = string
  description = "Criticality tier controlling auto-resolve and acknowledgement timeouts. critical = no auto-resolve, high = 4h, medium = 2h, low = 1h."
  default     = "high"

  validation {
    condition     = contains(["critical", "high", "medium", "low"], var.criticality_tier)
    error_message = "criticality_tier must be one of: critical, high, medium, low."
  }
}

variable "alert_grouping_timeout_seconds" {
  type        = number
  description = "Time window in seconds for grouping related alerts into a single incident. Default 300 (5 minutes)."
  default     = 300

  validation {
    condition     = var.alert_grouping_timeout_seconds >= 60 && var.alert_grouping_timeout_seconds <= 3600
    error_message = "alert_grouping_timeout_seconds must be between 60 and 3600."
  }
}

variable "create_datadog_integration" {
  type        = bool
  description = "Whether to create a Datadog service integration. Set to true if Datadog is sending alerts to this service."
  default     = false
}

variable "create_events_api_integration" {
  type        = bool
  description = "Whether to create a generic Events API v2 integration (for AlertManager, Grafana, or custom senders)."
  default     = true
}

variable "events_api_integration_name" {
  type        = string
  description = "Display name for the Events API v2 integration. Defaults to '<service_name>-events-api'."
  default     = null
}

variable "upstream_service_ids" {
  type        = list(string)
  description = "PagerDuty service IDs that this service depends on. Used to build the service dependency map for impact visualization."
  default     = []
}
