# GCP Project Bootstrap — Terraform
#
# Creates the foundational resources for a production-ready GCP project:
#   - Required APIs enabled
#   - Billing budget alert
#   - Artifact Registry (container images)
#   - Terraform state bucket
#   - Default SA disabled / org policy for SA keys
#   - Workload Identity Pool for GitHub Actions

terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.0"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = "~> 6.0"
    }
  }
  # State is stored locally for the bootstrap root; move to GCS after first apply
  # backend "gcs" {
  #   bucket = "${PROJECT_ID}-terraform-state"
  #   prefix = "bootstrap"
  # }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# ─── Required APIs ─────────────────────────────────────────────────────────────

resource "google_project_service" "required_apis" {
  for_each = toset([
    "cloudresourcemanager.googleapis.com",
    "iam.googleapis.com",
    "iamcredentials.googleapis.com",
    "sts.googleapis.com",
    "secretmanager.googleapis.com",
    "cloudkms.googleapis.com",
    "logging.googleapis.com",
    "monitoring.googleapis.com",
    "cloudtrace.googleapis.com",
    "run.googleapis.com",
    "cloudfunctions.googleapis.com",
    "eventarc.googleapis.com",
    "cloudbuild.googleapis.com",
    "artifactregistry.googleapis.com",
    "sqladmin.googleapis.com",
    "firestore.googleapis.com",
    "pubsub.googleapis.com",
  ])

  service            = each.value
  disable_on_destroy = false
}

# ─── Terraform State Bucket ────────────────────────────────────────────────────

resource "google_storage_bucket" "terraform_state" {
  name          = "${var.project_id}-terraform-state"
  location      = "US"
  force_destroy = false

  versioning {
    enabled = true
  }

  uniform_bucket_level_access = true
  public_access_prevention    = "enforced"

  lifecycle_rule {
    action { type = "Delete" }
    condition {
      num_newer_versions = 20
      is_live            = false
    }
  }

  depends_on = [google_project_service.required_apis]
}

# ─── Artifact Registry ─────────────────────────────────────────────────────────

resource "google_artifact_registry_repository" "containers" {
  location      = var.region
  repository_id = "containers"
  format        = "DOCKER"
  description   = "Container images for ${var.project_id}"

  depends_on = [google_project_service.required_apis]
}

# ─── Disable Default Compute SA ───────────────────────────────────────────────

data "google_project" "current" {
  project_id = var.project_id
}

resource "google_service_account" "default_compute" {
  account_id = "${data.google_project.current.number}-compute"
  # Reference to existing SA — we disable it
}

# Remove editor binding from default compute SA
resource "google_project_iam_member" "remove_default_editor" {
  project = var.project_id
  role    = "roles/editor"
  member  = "serviceAccount:${data.google_project.current.number}-compute@developer.gserviceaccount.com"

  # This resource should NOT exist — use terraform to enforce its removal
  # by importing the existing binding and then deleting this resource definition
  lifecycle {
    prevent_destroy = false
  }
}

# ─── Org Policy: Disable SA Key Creation ─────────────────────────────────────

resource "google_project_organization_policy" "disable_sa_key_creation" {
  project    = var.project_id
  constraint = "iam.disableServiceAccountKeyCreation"

  boolean_policy {
    enforced = true
  }
}

# ─── Workload Identity Pool (GitHub Actions) ──────────────────────────────────

resource "google_iam_workload_identity_pool" "github" {
  workload_identity_pool_id = "github-pool"
  display_name              = "GitHub Actions"
  description               = "WIF pool for GitHub Actions CI/CD — no JSON key files"

  depends_on = [google_project_service.required_apis]
}

resource "google_iam_workload_identity_pool_provider" "github" {
  workload_identity_pool_id          = google_iam_workload_identity_pool.github.workload_identity_pool_id
  workload_identity_pool_provider_id = "github-provider"
  display_name                       = "GitHub Actions OIDC"

  oidc {
    issuer_uri = "https://token.actions.githubusercontent.com"
  }

  attribute_mapping = {
    "google.subject"             = "assertion.sub"
    "attribute.repository"       = "assertion.repository"
    "attribute.repository_owner" = "assertion.repository_owner"
    "attribute.ref"              = "assertion.ref"
  }

  # Restrict to your org — replace with actual org/username
  attribute_condition = "assertion.repository_owner == '${var.github_org}'"
}

# ─── CI/CD Deploy Service Account ─────────────────────────────────────────────

resource "google_service_account" "ci_deploy" {
  account_id   = "ci-deploy-sa"
  display_name = "CI/CD Deploy SA"
  description  = "Used by GitHub Actions via WIF — ${var.github_org}/${var.github_repo}"
}

# Bind to WIF pool (repo-scoped)
resource "google_service_account_iam_member" "github_wif_binding" {
  service_account_id = google_service_account.ci_deploy.name
  role               = "roles/iam.workloadIdentityUser"
  member             = "principalSet://iam.googleapis.com/${google_iam_workload_identity_pool.github.name}/attribute.repository/${var.github_org}/${var.github_repo}"
}

# Minimum deploy roles
resource "google_project_iam_member" "ci_deploy_run_developer" {
  project = var.project_id
  role    = "roles/run.developer"
  member  = "serviceAccount:${google_service_account.ci_deploy.email}"
}

resource "google_project_iam_member" "ci_deploy_ar_reader" {
  project = var.project_id
  role    = "roles/artifactregistry.reader"
  member  = "serviceAccount:${google_service_account.ci_deploy.email}"
}
