output "service_id" {
  description = "PagerDuty service ID. Use for creating maintenance windows or additional integrations."
  value       = pagerduty_service.this.id
}

output "service_name" {
  description = "PagerDuty service name. Used in the Datadog @pagerduty-{name} handle."
  value       = pagerduty_service.this.name
}

# Primary output: consumed by observability Terraform modules.
# This is the routing_key (integration key) for Events API v2.
# Feed this into AlertManager kubernetes_secret or Datadog monitor message blocks.
output "integration_key" {
  description = "Events API v2 integration key (routing_key). Store in a secrets manager — never hardcode. Feed this into AlertManager config or Datadog monitor Terraform."
  value       = length(pagerduty_service_integration.events_api) > 0 ? pagerduty_service_integration.events_api[0].integration_key : null
  sensitive   = true
}

output "datadog_integration_key" {
  description = "Datadog integration key. Used in Datadog monitor @pagerduty-{service} handles. Only populated if create_datadog_integration = true."
  value       = length(pagerduty_service_integration.datadog) > 0 ? pagerduty_service_integration.datadog[0].integration_key : null
  sensitive   = true
}

output "html_url" {
  description = "URL to this PagerDuty service in the PD web UI."
  value       = pagerduty_service.this.html_url
}
