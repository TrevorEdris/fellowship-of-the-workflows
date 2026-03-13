output "workload_identity_provider" {
  description = "Full WIF provider resource name — use this in google-github-actions/auth"
  value       = google_iam_workload_identity_pool_provider.github.name
}

output "ci_deploy_service_account" {
  description = "CI/CD deploy service account email — use in google-github-actions/auth"
  value       = google_service_account.ci_deploy.email
}

output "artifact_registry_url" {
  description = "Container image registry URL"
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.containers.repository_id}"
}

output "terraform_state_bucket" {
  description = "GCS bucket for Terraform state"
  value       = google_storage_bucket.terraform_state.name
}
