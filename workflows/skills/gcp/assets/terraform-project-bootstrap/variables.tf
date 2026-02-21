variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "region" {
  description = "Default GCP region"
  type        = string
  default     = "us-central1"
}

variable "github_org" {
  description = "GitHub organization or username (for WIF attribute condition)"
  type        = string
}

variable "github_repo" {
  description = "GitHub repository name (without org prefix) for WIF binding"
  type        = string
}

variable "billing_budget_amount" {
  description = "Monthly billing budget alert threshold in USD"
  type        = number
  default     = 500
}
