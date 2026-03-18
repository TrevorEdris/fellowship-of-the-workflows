# IaC Decision Tree for GCP

## Which Tool to Use

| Scenario | Recommendation |
|----------|---------------|
| New project, no existing IaC | **Terraform** |
| Multi-cloud infrastructure | **Terraform** |
| Existing Terraform expertise | **Terraform** |
| GKE-native shop, GitOps-first, team familiar with Kubernetes | **Config Connector** |
| Existing Deployment Manager configs | Migrate with `DM Convert` tool → **Terraform** |
| Preview or beta GCP features | `hashicorp/google-beta` provider alongside `hashicorp/google` |
| Large organization with IaC modules needed | **Terraform** (module ecosystem is far more mature) |

**Deployment Manager is deprecated.** Google has stopped investing in it and recommends migrating to Terraform or Config Connector using the `DM Convert` tool (`gcloud deployment-manager dm-convert`).

## Terraform for GCP

### Provider Setup

```hcl
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
  backend "gcs" {
    bucket = "my-terraform-state"
    prefix = "my-project/prod"
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}
```

### Always Enable APIs Before Resources

```hcl
resource "google_project_service" "required_apis" {
  for_each = toset([
    "run.googleapis.com",
    "cloudresourcemanager.googleapis.com",
    "iam.googleapis.com",
    "secretmanager.googleapis.com",
    "artifactregistry.googleapis.com",
  ])
  service            = each.value
  disable_on_destroy = false
}

# Other resources depend on APIs being enabled
resource "google_cloud_run_v2_service" "app" {
  depends_on = [google_project_service.required_apis]
  # ...
}
```

### Service Account + Least Privilege Pattern

```hcl
resource "google_service_account" "app" {
  account_id   = "my-service"
  display_name = "My Service SA"
  description  = "Used by my-service Cloud Run deployment"
}

resource "google_project_iam_member" "app_sql_client" {
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.app.email}"
}

resource "google_project_iam_member" "app_secret_accessor" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.app.email}"
}
```

### Auth for Terraform Runs

| Context | Method |
|---------|--------|
| Local dev | ADC via `gcloud auth application-default login` |
| GitHub Actions CI | Workload Identity Federation (`google-github-actions/auth`) |
| GitLab CI | Workload Identity Federation (id_token support) |
| Self-hosted runner | Attached service account (GCE/GKE) |

Never use JSON key files in CI pipelines.

## Config Connector (KRM)

Config Connector is a Kubernetes operator that manages GCP resources as Kubernetes Custom Resources. Use it when:
- Your team is already operating GKE clusters
- You want GCP resources to be governed by Kubernetes RBAC
- Your GitOps tooling (ArgoCD, Flux) manages Kubernetes resources

```yaml
# Example: GCS bucket as a Kubernetes resource
apiVersion: storage.cnrm.cloud.google.com/v1beta1
kind: StorageBucket
metadata:
  name: my-bucket
  namespace: config-connector
  annotations:
    cnrm.cloud.google.com/project-id: my-project
spec:
  location: us-central1
  uniformBucketLevelAccess: true
```

**Cons vs Terraform:**
- GKE cluster required (overhead for non-GKE shops)
- Smaller module/community ecosystem
- Not multi-cloud

## Terraform Module Patterns for GCP

### Recommended Module Structure

```
modules/
  gcp-project-setup/
    main.tf        # API enablement, billing alert, org policy
    variables.tf
    outputs.tf
  gcp-cloud-run-service/
    main.tf        # Cloud Run service, SA, IAM bindings
    variables.tf
    outputs.tf
  gcp-cloud-sql/
    main.tf        # Cloud SQL instance, user, SA bindings
    variables.tf
    outputs.tf
```

### State Management

- Use GCS backend for state storage
- Enable versioning on the state bucket
- Use workspace separation for environments (dev/staging/prod)
- Lock state with GCS's native object locking

```hcl
# State bucket (bootstrap this manually or with a separate TF root)
resource "google_storage_bucket" "terraform_state" {
  name          = "${var.project_id}-terraform-state"
  location      = "US"
  force_destroy = false

  versioning {
    enabled = true
  }

  uniform_bucket_level_access = true
  public_access_prevention    = "enforced"
}
```
