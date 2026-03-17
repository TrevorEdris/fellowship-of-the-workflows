# ADC and Authentication

## Application Default Credentials (ADC) Lookup Order

ADC is the universal GCP authentication pattern. All Google client libraries use ADC automatically.

```
1. GOOGLE_APPLICATION_CREDENTIALS env var
   → Path to a service account JSON key file
   → Avoid in production — use only for local dev when other options fail

2. gcloud CLI ADC
   → ~/.config/gcloud/application_default_credentials.json
   → Set via: gcloud auth application-default login
   → Local development only — not available in containers

3. Attached service account (metadata server)
   → Automatically available on: Cloud Run, GKE pods, Compute Engine VMs, Cloud Functions
   → No credential files, no configuration needed
   → This is the preferred production auth method

4. Workload Identity Federation
   → OIDC token exchange for external workloads (GitHub Actions, GitLab CI, AWS)
   → No JSON key files required — preferred for all CI/CD pipelines
```

## Local Development: gcloud ADC

```bash
# Basic: authenticate as yourself (your Google account)
gcloud auth application-default login

# Preferred: impersonate a service account (closer to production auth)
gcloud auth application-default login \
  --impersonate-service-account=my-service-sa@PROJECT.iam.gserviceaccount.com

# Verify ADC is working and see which identity is being used
gcloud auth application-default print-access-token | head -c 50

# Clear ADC credentials
gcloud auth application-default revoke
```

## Production: Attached Service Account

Cloud Run, Cloud Functions, and GKE pods automatically receive credentials from the metadata server. No code changes required.

```go
// Go — no auth code needed; ADC picks up the metadata server
client, err := storage.NewClient(ctx)
```

```python
# Python — same
client = storage.Client()
```

Assign a custom service account at deploy time — do not use the default compute service account:

```bash
gcloud run deploy my-service \
  --service-account=my-service-sa@PROJECT.iam.gserviceaccount.com
```

## CI/CD: Workload Identity Federation

WIF eliminates JSON key files entirely. See `workload-identity-deep-dive.md` for full setup.

**GitHub Actions:**
```yaml
permissions:
  id-token: write

steps:
  - uses: google-github-actions/auth@v2
    with:
      workload_identity_provider: projects/NUMBER/locations/global/workloadIdentityPools/POOL/providers/PROVIDER
      service_account: deploy-sa@PROJECT.iam.gserviceaccount.com
```

## Service Account Impersonation

Impersonation allows you to act as a service account using your own credentials — useful for testing SA permissions locally without using key files.

```bash
# Impersonate a service account via ADC
gcloud auth application-default login \
  --impersonate-service-account=SA@PROJECT.iam.gserviceaccount.com

# Required IAM: your user account needs roles/iam.serviceAccountTokenCreator on the target SA
gcloud iam service-accounts add-iam-policy-binding SA@PROJECT.iam.gserviceaccount.com \
  --member=user:you@example.com \
  --role=roles/iam.serviceAccountTokenCreator
```

## Service Account Key Files: Anti-patterns and Risks

Key files are the most common GCP security mistake. Avoid them in all production contexts.

| Risk | Why It Matters |
|------|---------------|
| Keys in source control | Permanent credential exposure — keys don't expire automatically |
| Keys in CI env vars | Logged in CI outputs, accessible to any job in the pipeline |
| Keys on developer laptops | Lost device = compromised credentials |
| Long-lived keys without rotation | Keys valid for 10 years by default |
| Shared keys across services | One compromise affects all services |

**Enforce key prohibition at the org level:**
```bash
# Org policy: prevent key creation in the project
gcloud resource-manager org-policies set-policy \
  --project=PROJECT_ID policy.yaml

# policy.yaml:
# constraint: constraints/iam.disableServiceAccountKeyCreation
# booleanPolicy:
#   enforced: true
```

**When key files are unavoidable** (legacy systems, on-prem, non-GCP environments):
- Store in Secret Manager, not environment variables
- Rotate every 90 days maximum
- Create a dedicated SA with only the required roles
- Audit usage via Cloud Audit Logs
