# IAM Patterns

## Role Hierarchy

```
Primitive Roles (avoid)
  roles/owner      → Full control including billing and IAM
  roles/editor     → Create/modify most resources (excludes IAM)
  roles/viewer     → Read-only for all resources

Predefined Roles (use these)
  roles/run.admin      → Full Cloud Run control
  roles/run.developer  → Deploy, but not manage service config
  roles/run.invoker    → Call the service (HTTP invocation only)
  roles/cloudsql.client  → Connect to Cloud SQL (no management)
  ...etc per service

Custom Roles (when predefined don't fit)
  → Define in YAML, bind specific permissions
  → Use for: cross-service least privilege, org-specific access tiers
```

**Rule:** Bind the most specific predefined role. Only escalate to Editor/Owner when no predefined role suffices, and document why.

## Binding Patterns

### Project-Level Bindings

```bash
# Add binding
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member=serviceAccount:sa@project.iam.gserviceaccount.com \
  --role=roles/run.invoker

# Remove binding
gcloud projects remove-iam-policy-binding PROJECT_ID \
  --member=serviceAccount:sa@project.iam.gserviceaccount.com \
  --role=roles/run.invoker
```

### Resource-Level Bindings (Preferred for Least Privilege)

Binding at the resource level is more secure than project-level — only grants access to the specific resource.

```bash
# Cloud Run service-level invoker (preferred over project-level)
gcloud run services add-iam-policy-binding my-service \
  --region=us-central1 \
  --member=serviceAccount:caller-sa@PROJECT.iam.gserviceaccount.com \
  --role=roles/run.invoker

# GCS bucket-level (preferred over project storage admin)
gcloud storage buckets add-iam-policy-binding gs://my-bucket \
  --member=serviceAccount:app-sa@PROJECT.iam.gserviceaccount.com \
  --role=roles/storage.objectCreator

# Secret-level accessor (preferred over project-level)
gcloud secrets add-iam-policy-binding MY_SECRET \
  --member=serviceAccount:app-sa@PROJECT.iam.gserviceaccount.com \
  --role=roles/secretmanager.secretAccessor

# Pub/Sub topic-level publisher
gcloud pubsub topics add-iam-policy-binding my-topic \
  --member=serviceAccount:app-sa@PROJECT.iam.gserviceaccount.com \
  --role=roles/pubsub.publisher
```

## IAM Conditions

Conditions add attribute-based access control to bindings.

```bash
# Time-limited access (expires on a specific date)
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member=user:contractor@example.com \
  --role=roles/viewer \
  --condition='title=temp-access,expression=request.time < timestamp("2026-06-01T00:00:00Z")'

# Resource attribute condition (only Cloud Run services named "my-service")
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member=serviceAccount:sa@PROJECT.iam.gserviceaccount.com \
  --role=roles/run.admin \
  --condition='title=scoped-run-admin,expression=resource.name.startsWith("projects/_/locations/us-central1/services/my-service")'
```

## Custom Roles

```yaml
# custom-role.yaml
title: "App Deployer"
description: "Can deploy Cloud Run services but not manage IAM or delete services"
stage: GA
includedPermissions:
  - run.services.create
  - run.services.update
  - run.services.get
  - run.services.list
  - artifactregistry.repositories.get
  - artifactregistry.tags.get
```

```bash
# Create the custom role at project level
gcloud iam roles create AppDeployer \
  --project=PROJECT_ID \
  --file=custom-role.yaml

# Bind it
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member=serviceAccount:ci-deploy-sa@PROJECT.iam.gserviceaccount.com \
  --role=projects/PROJECT_ID/roles/AppDeployer
```

## Audit Logging

Enable Data Access audit logs to track who accessed what:

```python
# Audit log config for a project (set via Terraform or policy YAML)
auditConfigs:
  - service: "iam.googleapis.com"
    auditLogConfigs:
      - logType: ADMIN_READ
      - logType: DATA_READ
      - logType: DATA_WRITE
  - service: "secretmanager.googleapis.com"
    auditLogConfigs:
      - logType: DATA_ACCESS
```

```bash
# Query audit logs for IAM policy changes
gcloud logging read \
  "logName=\"projects/PROJECT/logs/cloudaudit.googleapis.com%2Factivity\" \
   AND protoPayload.methodName=\"SetIamPolicy\"" \
  --limit=20 \
  --format="table(timestamp,protoPayload.authenticationInfo.principalEmail,protoPayload.request.policy)"
```

## Common Permission Mappings

| Task | Predefined Role | Notes |
|------|----------------|-------|
| Invoke Cloud Run | `roles/run.invoker` | Per-service binding preferred |
| Deploy Cloud Run | `roles/run.developer` | Needs `roles/artifactregistry.reader` too |
| Connect to Cloud SQL | `roles/cloudsql.client` | Per-instance or project level |
| Read Cloud SQL schema | `roles/cloudsql.viewer` | For MCP and monitoring tools |
| Read GCS objects | `roles/storage.objectViewer` | Per-bucket binding preferred |
| Write GCS objects | `roles/storage.objectCreator` | Cannot delete — use objectUser for delete |
| Read/write/delete GCS | `roles/storage.objectUser` | Modern replacement for legacy roles |
| Read secrets | `roles/secretmanager.secretAccessor` | Per-secret binding preferred |
| Publish to Pub/Sub | `roles/pubsub.publisher` | Per-topic binding preferred |
| Subscribe to Pub/Sub | `roles/pubsub.subscriber` | Per-subscription binding preferred |
| Read Firestore | `roles/datastore.viewer` | Project level |
| Write Firestore | `roles/datastore.user` | Project level |
| Read Spanner | `roles/spanner.databaseReader` | Per-database binding |
| Write Spanner | `roles/spanner.databaseUser` | Per-database binding |
| Read KMS key | `roles/cloudkms.cryptoKeyDecrypter` | Per-key or per-keyring |
| Use KMS key for encryption | `roles/cloudkms.cryptoKeyEncrypterDecrypter` | Required for CMEK |

## Anti-patterns

| Anti-pattern | Consequence | Fix |
|-------------|-------------|-----|
| `roles/owner` on service accounts | Full project control, including billing and IAM | Least-privilege predefined roles |
| `roles/editor` on service accounts | Can modify most resources, escalate to other services | Specific predefined roles |
| Project-level binding when resource-level suffices | Over-broad access | Bind at resource level |
| No conditions on time-limited access | Contractor/temp access never expires | Add time-based IAM condition |
| `allUsers` binding | Public access without authentication | Remove; use `--no-allow-unauthenticated` on Cloud Run |
| Primitive roles for new bindings | Overly broad, not auditable | Always use predefined or custom roles |
