---
name: gcp
description: "GCP project setup, authentication (ADC/Workload Identity), gcloud CLI patterns, IaC decision tree, MCP server configuration, and SDK quick-starts. Entry point for all GCP work — use /cloud-run, /gcp-data, or /gcp-iam for deep-domain tasks."
context: fork
allowed-tools: Bash, Read, Glob, Grep
model: sonnet
argument-hint: "[auth|setup|iac|mcp|sdk]"
tags: [gcp]
---

# GCP

Bootstrap and operate Google Cloud Platform projects with correct authentication, tooling, and IaC patterns.

---

## When to Use

- Setting up a new GCP project or configuring local dev credentials
- Deciding between Terraform, Config Connector, and Deployment Manager
- Configuring gcloud named configurations for multi-project work
- Setting up MCP servers for AI agent access to GCP services
- Getting the right SDK quick-start for your language

For domain-specific work, route to the specialized skills:
- `/cloud-run` — Cloud Run services/jobs, Cloud Functions, Eventarc, Pub/Sub
- `/gcp-data` — Cloud SQL, Firestore, GCS, Spanner, Memorystore
- `/gcp-iam` — IAM roles, service accounts, Secret Manager, KMS, Workload Identity

---

## Quick Start

```
/gcp auth      # Set up ADC, Workload Identity, SA impersonation
/gcp setup     # New project bootstrap: APIs, billing alerts, org policy
/gcp iac       # IaC decision tree: Terraform vs Config Connector
/gcp mcp       # Configure GCP MCP servers for AI agent workflows
/gcp sdk       # Language-specific client library quick-start
```

---

## Context

ACTIVE GCLOUD CONFIG:
```
!`gcloud config list 2>/dev/null || echo "gcloud CLI not found — install from https://cloud.google.com/sdk/docs/install"`
```

ACTIVE PROJECT:
```
!`gcloud config get-value project 2>/dev/null || echo "no active project"`
```

ENABLED APIS (top 20):
```
!`gcloud services list --enabled --limit=20 --format="value(config.name)" 2>/dev/null || echo "unable to list APIs"`
```

LOCAL ADC STATUS:
```
!`gcloud auth application-default print-access-token 2>/dev/null | head -c 20 && echo "... (ADC active)" || echo "ADC not configured — run: gcloud auth application-default login"`
```

---

## Mode: auth

Configure authentication for the correct context.

### ADC Lookup Order (universal — memorize this)

```
1. GOOGLE_APPLICATION_CREDENTIALS env var → JSON key file (avoid in prod)
2. gcloud CLI ADC → ~/.config/gcloud/application_default_credentials.json (local dev only)
3. Attached service account → metadata server (Cloud Run, GKE, Compute Engine — preferred for prod)
4. Workload Identity Federation → OIDC token exchange (CI/CD — preferred for pipelines)
```

### Local Dev Setup

```bash
# Interactive login for local dev
gcloud auth application-default login

# Impersonate a scoped service account (preferred over full-admin ADC)
gcloud auth application-default login \
  --impersonate-service-account=deploy-sa@PROJECT_ID.iam.gserviceaccount.com

# Verify ADC is working
gcloud auth application-default print-access-token
```

### CI/CD: GitHub Actions + Workload Identity Federation

```yaml
# In your workflow — no JSON keys needed
- uses: google-github-actions/auth@v2
  with:
    workload_identity_provider: projects/PROJECT_NUMBER/locations/global/workloadIdentityPools/POOL/providers/PROVIDER
    service_account: deploy-sa@PROJECT_ID.iam.gserviceaccount.com
```

See `assets/workload-identity-gh-actions.yaml` for the complete GCP-side setup.

### Anti-patterns

- Service account JSON keys in repos or CI environment variables
- Using `gcloud auth login` user credentials in production
- `GOOGLE_APPLICATION_CREDENTIALS` pointing to a JSON key in production
- Owner/Editor roles for service accounts

---

## Mode: setup

Bootstrap a new GCP project with production-safe defaults.

**Steps:**
1. Create or select project: `gcloud projects create PROJECT_ID --name="Display Name"`
2. Link billing: `gcloud billing projects link PROJECT_ID --billing-account=BILLING_ACCOUNT_ID`
3. Enable required APIs (always start with these):
   ```bash
   gcloud services enable \
     cloudresourcemanager.googleapis.com \
     iam.googleapis.com \
     iamcredentials.googleapis.com \
     secretmanager.googleapis.com \
     run.googleapis.com \
     cloudbuild.googleapis.com \
     artifactregistry.googleapis.com \
     --project=PROJECT_ID
   ```
4. Create a billing alert (critical — prevents surprise bills):
   ```bash
   # Via Terraform — see assets/terraform-project-bootstrap/
   # Or manually in Console: Billing > Budgets & Alerts
   ```
5. Restrict the default service account: disable or constrain `Compute Engine default service account`
6. Configure org policy: `constraints/iam.disableServiceAccountKeyCreation` (blocks key files)

See `references/gcp-project-setup-checklist.md` for the full checklist.

---

## Mode: iac

Select the right IaC tool for GCP.

| Scenario | Recommended Tool |
|----------|-----------------|
| New project, any team | **Terraform** (`hashicorp/google` provider) |
| GKE-native shop, GitOps-first | Config Connector (KRM) |
| Existing Terraform expertise | **Terraform** |
| Migration from Deployment Manager | `DM Convert` tool → Terraform |
| Preview features | `hashicorp/google-beta` provider alongside `hashicorp/google` |

**Deployment Manager: do not use for new projects.** Google is sunsetting it. Use `DM Convert` to migrate existing configs.

**Terraform pattern for GCP:**
```hcl
# Always enable APIs before resources
resource "google_project_service" "run" {
  service = "run.googleapis.com"
  disable_on_destroy = false
}

# Service account with least privilege
resource "google_service_account" "app" {
  account_id = "my-service"
}

resource "google_project_iam_member" "app_invoker" {
  role   = "roles/run.invoker"
  member = "serviceAccount:${google_service_account.app.email}"
}
```

See `assets/terraform-project-bootstrap/` for a complete bootstrap module.
See `references/iac-decision-tree.md` for detailed comparison.

---

## Mode: mcp

Configure GCP MCP servers for AI agent workflows.

### Official Google-Managed Remote MCPs (preferred)

These run on Google infrastructure with IAM controls — no key files required.

| Service | Status | Setup |
|---------|--------|-------|
| BigQuery | GA | `gcloud alpha bq mcp-server setup` |
| Compute Engine | GA | [Console → AI → MCP Servers] |
| GKE | GA | [Console → AI → MCP Servers] |
| Cloud SQL | Preview | Opt-in via Console |
| AlloyDB | Preview | Opt-in via Console |
| Spanner | Preview | Opt-in via Console |

### gcloud-mcp (self-hosted, official)

```json
{
  "mcpServers": {
    "gcloud": {
      "command": "gcloud",
      "args": ["alpha", "mcp-server", "run"],
      "env": {
        "CLOUDSDK_CORE_PROJECT": "your-project-id"
      }
    }
  }
}
```

Impersonate a scoped SA instead of using your full admin account:
```bash
gcloud auth application-default login \
  --impersonate-service-account=mcp-agent-sa@PROJECT.iam.gserviceaccount.com
```

See `references/mcp-config.md` for community MCPs, security notes, and full config examples.

---

## Mode: sdk

Language-specific GCP client library quick-starts using ADC.

### Go

```go
import "cloud.google.com/go/storage"

// ADC automatic — no credential code needed
client, err := storage.NewClient(ctx)
if err != nil {
    return fmt.Errorf("storage.NewClient: %w", err)
}
defer client.Close()
```

### Python

```python
from google.cloud import storage

# ADC automatic
client = storage.Client()
```

### Node.js / TypeScript

```typescript
import { Storage } from '@google-cloud/storage';

// ADC automatic
const storage = new Storage();
```

See the language-specific `gcp-clients.md` in each `*-patterns` skill for full patterns, error handling, and retry config.

---

## Overlap and Cross-References

| Topic | Where It Lives |
|-------|---------------|
| Cloud Run deployment | `/cloud-run` skill |
| Cloud Build / Cloud Deploy pipelines | `/cicd-pipeline` skill (GCP deploy mode) |
| Cloud Monitoring / Logging / Trace | `/observability` skill (Cloud Monitoring routing path) |
| IAM, Secret Manager, KMS | `/gcp-iam` skill |
| Cloud SQL, Firestore, GCS | `/gcp-data` skill |
| Go GCP client patterns | `go-patterns/references/gcp-clients.md` |
| Python GCP client patterns | `python-patterns/references/gcp-clients.md` |
| TypeScript GCP client patterns | `typescript-patterns/references/gcp-clients.md` |

---

## References

- `references/adc-and-auth.md` — ADC lookup order, Workload Identity, SA impersonation, key file risks
- `references/iac-decision-tree.md` — Terraform vs Config Connector vs Deployment Manager
- `references/gcloud-cli-patterns.md` — Named configurations, common command patterns
- `references/mcp-config.md` — Official MCPs, gcloud-mcp setup, community MCPs, security notes
- `references/gcp-project-setup-checklist.md` — New project bootstrap checklist

## Assets

- `assets/workload-identity-gh-actions.yaml` — OIDC trust config for GitHub Actions → GCP
- `assets/terraform-project-bootstrap/` — Minimal TF for project + SA + API enablement
