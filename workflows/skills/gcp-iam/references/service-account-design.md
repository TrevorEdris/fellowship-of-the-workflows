# Service Account Design

## Principles

1. **One SA per service** — never share a service account between different workloads.
2. **Least privilege** — bind only the roles that service actually needs.
3. **No key files** — use metadata server (Cloud Run, GKE) or Workload Identity (CI/CD).
4. **Disable the default compute SA** — it has Editor-equivalent scope.
5. **Document each SA** — use `--description` to capture purpose and owner.

## SA Naming Convention

```
{service}-{function}-sa@{project}.iam.gserviceaccount.com

Examples:
  orders-service-sa@my-project.iam.gserviceaccount.com
  orders-migrator-sa@my-project.iam.gserviceaccount.com
  ci-deploy-sa@my-project.iam.gserviceaccount.com
  mcp-agent-sa@my-project.iam.gserviceaccount.com
```

## Creating and Binding

```bash
# Create
gcloud iam service-accounts create orders-service-sa \
  --display-name="Orders Service SA" \
  --description="Cloud Run orders-service — Cloud SQL client + Secret Manager reader"

# Bind least-privilege roles
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member=serviceAccount:orders-service-sa@PROJECT.iam.gserviceaccount.com \
  --role=roles/cloudsql.client

# Prefer resource-level bindings over project-level
gcloud secrets add-iam-policy-binding db-password \
  --member=serviceAccount:orders-service-sa@PROJECT.iam.gserviceaccount.com \
  --role=roles/secretmanager.secretAccessor

# Attach to Cloud Run service
gcloud run deploy orders-service \
  --service-account=orders-service-sa@PROJECT.iam.gserviceaccount.com
```

## Default Compute Service Account (Disable It)

The Compute Engine default SA (`PROJECT_NUMBER-compute@developer.gserviceaccount.com`) is automatically bound to `roles/editor`. This means any Cloud Run service or GKE pod that doesn't explicitly specify a service account inherits Editor-level access.

```bash
# Check if default SA is used anywhere
gcloud run services list --format="table(metadata.name,spec.template.spec.serviceAccountName)" | \
  grep -v "custom-sa"  # Highlight services not using a custom SA

# Disable the default SA (cleanest option for greenfield projects)
gcloud iam service-accounts disable \
  PROJECT_NUMBER-compute@developer.gserviceaccount.com \
  --project=PROJECT_ID

# OR: Remove the Editor binding (keeps SA enabled but removes over-privilege)
gcloud projects remove-iam-policy-binding PROJECT_ID \
  --member=serviceAccount:PROJECT_NUMBER-compute@developer.gserviceaccount.com \
  --role=roles/editor
```

## Service Account Impersonation

Impersonation allows one SA (or a user) to act as another SA without generating a key file.

```bash
# Grant impersonation permission
gcloud iam service-accounts add-iam-policy-binding target-sa@PROJECT.iam.gserviceaccount.com \
  --member=serviceAccount:source-sa@PROJECT.iam.gserviceaccount.com \
  --role=roles/iam.serviceAccountTokenCreator

# Use impersonation via gcloud (local dev)
gcloud auth application-default login \
  --impersonate-service-account=target-sa@PROJECT.iam.gserviceaccount.com

# Use impersonation in code (Go)
import "google.golang.org/api/impersonate"

ts, err := impersonate.CredentialsTokenSource(ctx, impersonate.CredentialsConfig{
    TargetPrincipal: "target-sa@PROJECT.iam.gserviceaccount.com",
    Scopes:          []string{"https://www.googleapis.com/auth/cloud-platform"},
})
```

**Common impersonation use cases:**
- CI/CD pipeline SA impersonates a more restricted deployment SA
- Developer impersonates a service SA to reproduce production auth behavior locally
- Audit: test what a service SA can and cannot do

## Service Account Key Files (Emergency Use Only)

Key files are a last resort. When unavoidable:

```bash
# Create a key file
gcloud iam service-accounts keys create key.json \
  --iam-account=sa@PROJECT.iam.gserviceaccount.com

# List existing keys (should be zero in production)
gcloud iam service-accounts keys list \
  --iam-account=sa@PROJECT.iam.gserviceaccount.com \
  --managed-by=user

# Delete a key (immediate revocation)
gcloud iam service-accounts keys delete KEY_ID \
  --iam-account=sa@PROJECT.iam.gserviceaccount.com
```

**If you must use key files:**
- Store in Secret Manager, not in config files or env vars
- Rotate every 90 days
- Alert on key age > 90 days via Security Command Center
- Use `GOOGLE_APPLICATION_CREDENTIALS` pointing to a file path, never to inline JSON
- Set an org policy to block future key creation: `constraints/iam.disableServiceAccountKeyCreation`

## SA Lifecycle Management

```bash
# Disable SA (blocks all auth without deleting)
gcloud iam service-accounts disable old-sa@PROJECT.iam.gserviceaccount.com

# Re-enable
gcloud iam service-accounts enable old-sa@PROJECT.iam.gserviceaccount.com

# Delete SA (permanent — removes all bindings)
gcloud iam service-accounts delete old-sa@PROJECT.iam.gserviceaccount.com

# List all SAs in project
gcloud iam service-accounts list --format="table(email,disabled,description)"

# Find SAs with no recent activity (Security Command Center or gcloud recommender)
gcloud recommender recommendations list \
  --recommender=google.iam.policy.Recommender \
  --location=global \
  --project=PROJECT_ID
```

## Terraform SA Pattern

```hcl
# Create SA
resource "google_service_account" "orders_service" {
  account_id   = "orders-service-sa"
  display_name = "Orders Service SA"
  description  = "Cloud Run orders-service — Cloud SQL client"
}

# Bind roles
resource "google_project_iam_member" "orders_sql_client" {
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.orders_service.email}"
}

# Resource-level binding (preferred)
resource "google_secret_manager_secret_iam_member" "orders_db_password" {
  secret_id = google_secret_manager_secret.db_password.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.orders_service.email}"
}

# Disallow key creation at org level
resource "google_project_organization_policy" "disable_sa_key_creation" {
  project    = var.project_id
  constraint = "iam.disableServiceAccountKeyCreation"
  boolean_policy {
    enforced = true
  }
}
```
