# gcloud CLI Patterns

## Named Configurations (Multi-Project / Multi-Account)

Named configurations let you switch between projects, regions, and accounts without re-authenticating.

```bash
# Create a named config for each environment
gcloud config configurations create dev
gcloud config configurations create staging
gcloud config configurations create prod

# Configure each
gcloud config set project my-project-dev --configuration=dev
gcloud config set compute/region us-central1 --configuration=dev
gcloud config set account dev-user@example.com --configuration=dev

# Activate a config
gcloud config configurations activate dev

# List all configs
gcloud config configurations list

# Show current active config
gcloud config list
```

**Use named configs instead of re-running `gcloud config set project` constantly.** A misapplied project switch is a common cause of destructive operations on the wrong project.

## Verify Before Destructive Operations

```bash
# Always run this before any destructive gcloud command
gcloud config list
# Verify: account, project, and region are what you expect

# Example: before deleting a Cloud Run service
gcloud config get-value project   # confirm project
gcloud run services describe SERVICE_NAME --region=REGION  # confirm service
gcloud run services delete SERVICE_NAME --region=REGION
```

## Project Switching

```bash
# Switch project in current config
gcloud config set project PROJECT_ID

# Prefer the --project flag for one-off commands (doesn't affect config)
gcloud run services list --project=other-project --region=us-central1

# Use $(gcloud config get-value project) in scripts to avoid hardcoded IDs
PROJECT=$(gcloud config get-value project)
gcloud sql instances list --project="$PROJECT"
```

## Service Account Impersonation for Least-Privilege Local Dev

```bash
# Impersonate a scoped service account instead of using your full admin credentials
gcloud auth application-default login \
  --impersonate-service-account=deploy-sa@PROJECT.iam.gserviceaccount.com

# Verify which identity is active
curl -s -H "Authorization: Bearer $(gcloud auth application-default print-access-token)" \
  "https://www.googleapis.com/oauth2/v1/tokeninfo" | python3 -m json.tool
```

## Enabling APIs

APIs must be enabled before resources can be created. Always check before provisioning.

```bash
# Enable a single API
gcloud services enable run.googleapis.com

# Enable multiple at once
gcloud services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com \
  secretmanager.googleapis.com \
  iam.googleapis.com

# Check if an API is enabled
gcloud services list --enabled --filter="name:run.googleapis.com"

# List all enabled APIs
gcloud services list --enabled --format="value(config.name)" | sort
```

## IAM Policy Inspection

```bash
# View project IAM policy
gcloud projects get-iam-policy PROJECT_ID

# Filter: who has a specific role
gcloud projects get-iam-policy PROJECT_ID \
  --flatten="bindings[].members" \
  --filter="bindings.role=roles/run.admin" \
  --format="value(bindings.members)"

# Filter: what roles does a principal have
gcloud projects get-iam-policy PROJECT_ID \
  --flatten="bindings[].members" \
  --filter="bindings.members:sa@project.iam.gserviceaccount.com" \
  --format="table(bindings.role)"
```

## Cloud Storage: gcloud storage vs gsutil

`gcloud storage` is the modern replacement for `gsutil`. Use it for all new scripts.

```bash
# Copy (prefer gcloud storage over gsutil cp)
gcloud storage cp local-file.txt gs://BUCKET/path/

# Recursive sync (replaces gsutil rsync)
gcloud storage rsync --recursive src/ gs://BUCKET/prefix/

# List bucket contents
gcloud storage ls gs://BUCKET/path/

# Delete objects
gcloud storage rm gs://BUCKET/path/file.txt
```

## Logging and Diagnostics

```bash
# Tail Cloud Run logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=SERVICE_NAME" \
  --limit=50 \
  --format="table(timestamp,textPayload)"

# Stream logs (follow mode)
gcloud alpha logging tail "resource.type=cloud_run_revision" \
  --format="value(textPayload)"

# Read Cloud Function logs
gcloud functions logs read FUNCTION_NAME --gen2 --limit=20

# View recent operations (audit trail)
gcloud logging read "logName=projects/PROJECT/logs/cloudaudit.googleapis.com%2Factivity" \
  --limit=20 \
  --format="table(timestamp,protoPayload.authenticationInfo.principalEmail,protoPayload.methodName)"
```

## Anti-patterns

| Anti-pattern | Better approach |
|-------------|----------------|
| `gcloud config set project` in scripts | Use `--project` flag or `$(gcloud config get-value project)` |
| Hardcoded project IDs in shell scripts | `PROJECT=$(gcloud config get-value project)` |
| `gcloud` without `--quiet` in automation | Add `--quiet` to suppress interactive prompts |
| `gcloud` in production container | Use metadata server (ADC) — don't install gcloud in containers |
| Using `gsutil` in new scripts | Use `gcloud storage` instead |
| Running as full admin user in CI/CD | Impersonate a scoped service account or use Workload Identity |
