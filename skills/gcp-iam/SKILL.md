---
name: gcp-iam
description: "Audit and configure GCP IAM: roles/bindings, service accounts, Workload Identity Federation, Secret Manager, KMS (CMEK), and VPC Service Controls. Use when setting up least-privilege access, rotating secrets, or hardening GCP security posture."
context: fork
agent: gcp-iam-auditor
allowed-tools: Bash, Read, Glob, Grep, Write
model: sonnet
argument-hint: "[audit|service-accounts|bindings|wif|secrets|kms|vpc-sc]"
tags: [gcp, security]
---

# GCP IAM

Configure least-privilege IAM, service accounts, secrets, and encryption for GCP workloads.

---

## When to Use

- Auditing IAM policies for over-privileged roles or exposed service accounts
- Designing per-service service accounts with least-privilege roles
- Setting up Workload Identity Federation for CI/CD (GitHub Actions, GitLab)
- Configuring Secret Manager for application secrets
- Enabling CMEK (Customer-Managed Encryption Keys) via KMS
- Configuring VPC Service Controls to restrict API access by perimeter

---

## Quick Start

```
/gcp-iam audit           # Audit current IAM policy for over-privilege, key files, default SA abuse
/gcp-iam service-accounts # Design and create per-service service accounts
/gcp-iam bindings         # Add/review IAM role bindings
/gcp-iam wif              # Workload Identity Federation for GitHub Actions / GitLab / AWS
/gcp-iam secrets          # Secret Manager: create, version, rotate, access audit
/gcp-iam kms              # KMS CMEK for GCS, Cloud SQL, GKE, Pub/Sub
/gcp-iam vpc-sc           # VPC Service Controls perimeter setup
```

---

## Context

ACTIVE PROJECT:
```
!`gcloud config get-value project 2>/dev/null || echo "no active project"`
```

CURRENT IAM POLICY (project level):
```
!`gcloud projects get-iam-policy $(gcloud config get-value project 2>/dev/null) --format=json 2>/dev/null | python3 -c "import json,sys; p=json.load(sys.stdin); [print(b['role'], '->', b.get('members',[])) for b in p.get('bindings',[])]" 2>/dev/null | head -30 || echo "unable to fetch IAM policy"`
```

SERVICE ACCOUNTS:
```
!`gcloud iam service-accounts list --format="table(email,disabled)" 2>/dev/null | head -20 || echo "unable to list"`
```

SERVICE ACCOUNT KEYS (key files are a risk):
```
!`gcloud iam service-accounts list --format="value(email)" 2>/dev/null | while read sa; do keys=$(gcloud iam service-accounts keys list --iam-account="$sa" --managed-by=user --format="value(name)" 2>/dev/null | wc -l); [ "$keys" -gt 0 ] && echo "$sa has $keys user-managed key(s)"; done 2>/dev/null || echo "unable to check"`
```

---

## Mode: audit

Review IAM policy for common security issues.

**Audit checklist:**

```bash
# Check for primitives (Owner/Editor/Viewer on principals that should use predefined roles)
gcloud projects get-iam-policy PROJECT_ID \
  --flatten="bindings[].members" \
  --filter="bindings.role:(roles/owner OR roles/editor)" \
  --format="table(bindings.role, bindings.members)"

# Check for allUsers or allAuthenticatedUsers
gcloud projects get-iam-policy PROJECT_ID \
  --flatten="bindings[].members" \
  --filter="bindings.members:(allUsers OR allAuthenticatedUsers)" \
  --format="table(bindings.role, bindings.members)"

# List user-managed service account keys (should be zero in production)
gcloud iam service-accounts list --format="value(email)" | \
  xargs -I{} gcloud iam service-accounts keys list \
    --iam-account={} --managed-by=user --format="value(name)" 2>/dev/null
```

**Critical findings (CRITICAL):**
- `roles/owner` or `roles/editor` on service accounts
- `allUsers` or `allAuthenticatedUsers` on any binding
- User-managed service account keys in production
- Default compute service account used by workloads (has broad Editor-equivalent scope)
- Service accounts with `roles/iam.serviceAccountTokenCreator` on themselves

**High priority (HIGH):**
- Primitive roles (`roles/viewer`) where predefined roles suffice
- Service accounts without `--description` (undocumented purpose)
- Single service account used by multiple services (breaks blast radius)
- Missing org policy `constraints/iam.disableServiceAccountKeyCreation`

See `references/iam-patterns.md` for detailed role hierarchy and recommended role mappings.

---

## Mode: service-accounts

Design and provision per-service service accounts.

### Principles

- **One service account per service** — never share between different workloads.
- **Least privilege** — bind only the roles required by that service.
- **No key files** — use metadata server (Cloud Run/GKE) or Workload Identity (CI/CD).
- **Disable the default compute SA** — it has broad Editor-equivalent scope.

```bash
# Create a service account
gcloud iam service-accounts create my-service-sa \
  --display-name="My Service SA" \
  --description="Used by my-service Cloud Run service — Cloud SQL client only"

# Grant least-privilege role (example: Cloud SQL client)
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member=serviceAccount:my-service-sa@PROJECT.iam.gserviceaccount.com \
  --role=roles/cloudsql.client

# Bind to Cloud Run service
gcloud run deploy my-service \
  --service-account=my-service-sa@PROJECT.iam.gserviceaccount.com

# Disable key creation at org level (enforce via org policy)
gcloud resource-manager org-policies set-policy \
  --project=PROJECT_ID \
  iam-disable-sa-key-creation.yaml
```

See `references/service-account-design.md` for per-role mappings and impersonation patterns.

---

## Mode: bindings

Add or review IAM role bindings at project, folder, or resource level.

```bash
# Add a binding
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member=serviceAccount:SA@PROJECT.iam.gserviceaccount.com \
  --role=roles/run.invoker

# Add a binding with condition (time-limited)
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member=user:eng@example.com \
  --role=roles/viewer \
  --condition='expression=request.time < timestamp("2026-06-01T00:00:00Z"),title=temp-access'

# Remove a binding
gcloud projects remove-iam-policy-binding PROJECT_ID \
  --member=serviceAccount:SA@PROJECT.iam.gserviceaccount.com \
  --role=roles/editor

# Audit: show who has a specific role
gcloud projects get-iam-policy PROJECT_ID \
  --flatten="bindings[].members" \
  --filter="bindings.role=roles/run.admin" \
  --format="value(bindings.members)"
```

**Common least-privilege role mappings:**

| Task | Role |
|------|------|
| Call Cloud Run service | `roles/run.invoker` |
| Deploy to Cloud Run | `roles/run.developer` |
| Read from GCS bucket | `roles/storage.objectViewer` |
| Read/write GCS objects | `roles/storage.objectUser` |
| Connect to Cloud SQL | `roles/cloudsql.client` |
| Read secrets | `roles/secretmanager.secretAccessor` |
| Pub/Sub publish | `roles/pubsub.publisher` |
| Pub/Sub subscribe | `roles/pubsub.subscriber` |
| Read from Firestore | `roles/datastore.viewer` |

---

## Mode: wif

Configure Workload Identity Federation for keyless CI/CD authentication.

### GitHub Actions → GCP (recommended)

**Step 1: Create Workload Identity Pool and Provider (one-time)**

```bash
# Create the pool
gcloud iam workload-identity-pools create github-pool \
  --location=global \
  --display-name="GitHub Actions Pool"

# Create the OIDC provider
gcloud iam workload-identity-pools providers create-oidc github-provider \
  --location=global \
  --workload-identity-pool=github-pool \
  --issuer-uri="https://token.actions.githubusercontent.com" \
  --attribute-mapping="google.subject=assertion.sub,attribute.repository=assertion.repository,attribute.actor=assertion.actor" \
  --attribute-condition="assertion.repository_owner=='YOUR_ORG'"
```

**Step 2: Bind service account to the pool**

```bash
# Get the pool resource name
POOL=$(gcloud iam workload-identity-pools describe github-pool \
  --location=global --format="value(name)")

# Allow GitHub Actions for a specific repo to impersonate the SA
gcloud iam service-accounts add-iam-policy-binding \
  deploy-sa@PROJECT.iam.gserviceaccount.com \
  --role=roles/iam.workloadIdentityUser \
  --member="principalSet://iam.googleapis.com/${POOL}/attribute.repository/YOUR_ORG/YOUR_REPO"
```

**Step 3: Use in GitHub Actions workflow**

```yaml
permissions:
  id-token: write
  contents: read

steps:
  - uses: google-github-actions/auth@v2
    with:
      workload_identity_provider: projects/PROJECT_NUMBER/locations/global/workloadIdentityPools/github-pool/providers/github-provider
      service_account: deploy-sa@PROJECT_ID.iam.gserviceaccount.com
```

See `references/workload-identity-deep-dive.md` for GitLab CI, AWS, and on-prem federation.
See `/gcp/assets/workload-identity-gh-actions.yaml` for the reusable OIDC trust config template.

---

## Mode: secrets

Manage application secrets in Secret Manager.

```bash
# Create a secret
echo -n "my-secret-value" | gcloud secrets create MY_SECRET \
  --data-file=- \
  --replication-policy=automatic

# Add a new version
echo -n "new-value" | gcloud secrets versions add MY_SECRET --data-file=-

# Grant access to a service account
gcloud secrets add-iam-policy-binding MY_SECRET \
  --member=serviceAccount:app-sa@PROJECT.iam.gserviceaccount.com \
  --role=roles/secretmanager.secretAccessor

# Inject into Cloud Run (no SDK code needed)
gcloud run services update SERVICE_NAME \
  --set-secrets=DB_PASSWORD=MY_SECRET:latest

# Access programmatically (avoid — prefer --set-secrets on Cloud Run)
gcloud secrets versions access latest --secret=MY_SECRET
```

**Rotation:**

```bash
# Add a new version and disable the old one
echo -n "rotated-value" | gcloud secrets versions add MY_SECRET --data-file=-
gcloud secrets versions disable PREVIOUS_VERSION_ID --secret=MY_SECRET
```

See `references/secret-manager-patterns.md` for audit logging, rotation automation, and cross-project access.

---

## Mode: kms

Configure Customer-Managed Encryption Keys (CMEK) for GCP services.

```bash
# Create a key ring and key
gcloud kms keyrings create my-keyring --location=REGION

gcloud kms keys create my-key \
  --keyring=my-keyring \
  --location=REGION \
  --purpose=encryption \
  --rotation-period=90d \
  --next-rotation-time=$(date -d "+90 days" --iso-8601)

# Grant Cloud SQL service account permission to use the key
gcloud kms keys add-iam-policy-binding my-key \
  --keyring=my-keyring \
  --location=REGION \
  --member=serviceAccount:service-PROJECT_NUMBER@gcp-sa-cloud-sql.iam.gserviceaccount.com \
  --role=roles/cloudkms.cryptoKeyEncrypterDecrypter

# Enable CMEK on Cloud SQL (at instance creation)
gcloud sql instances create INSTANCE \
  --disk-encryption-key=projects/PROJECT/locations/REGION/keyRings/my-keyring/cryptoKeys/my-key
```

**CMEK support matrix:**

| Service | CMEK Support |
|---------|-------------|
| Cloud Storage | Yes — per bucket |
| Cloud SQL | Yes — per instance |
| GKE (etcd + node disk) | Yes — at cluster creation |
| Pub/Sub | Yes — per topic |
| Cloud Run | Artifact Registry only |
| Firestore | Yes — per database |

See `references/kms-patterns.md` for key rotation, destruction protection, and audit logging.

---

## Verification Checklist

- [ ] No `roles/owner` or `roles/editor` on service accounts
- [ ] No `allUsers` or `allAuthenticatedUsers` in IAM policy
- [ ] Zero user-managed service account keys in production
- [ ] Default compute service account disabled or bound to no roles
- [ ] Each service has its own service account
- [ ] Secrets stored in Secret Manager, not environment variables
- [ ] Workload Identity Federation configured for CI/CD (no JSON keys in pipelines)
- [ ] KMS rotation period set for CMEK keys
- [ ] Secret Manager audit logs enabled
- [ ] IAM conditions used for time-limited or resource-scoped access

---

## References

- `references/iam-patterns.md` — Role binding patterns, custom roles, conditions, audit logging
- `references/service-account-design.md` — Per-service SA, least-privilege, impersonation
- `references/secret-manager-patterns.md` — Versioning, rotation, cross-project access, audit
- `references/kms-patterns.md` — CMEK setup, key rotation, destruction protection
- `references/workload-identity-deep-dive.md` — WIF for GitHub Actions, GitLab, AWS, on-prem
