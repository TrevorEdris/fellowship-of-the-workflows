# Workload Identity Federation Deep Dive

## What is WIF?

Workload Identity Federation lets external workloads (GitHub Actions, GitLab CI, AWS, on-prem) exchange their native OIDC/SAML tokens for short-lived GCP access tokens — without JSON key files.

```
External Identity          GCP WIF                   GCP Service Account
GitHub Actions OIDC  →  Token Exchange  →  Short-lived GCP token
GitLab CI JWT        →  Token Exchange  →  Short-lived GCP token
AWS Credentials      →  Token Exchange  →  Short-lived GCP token
```

## Core Concepts

| Concept | Description |
|---------|-------------|
| **Workload Identity Pool** | Container for external identity providers |
| **Provider** | Configuration for an OIDC or SAML identity source |
| **Attribute Mapping** | Maps claims from external token to Google attributes |
| **Attribute Condition** | Expression that must be true to allow exchange |
| **Principal** | The external identity (e.g., `assertion.sub`) |
| **SA Impersonation** | The WIF principal impersonates a GCP service account |

## GitHub Actions Setup (Most Common)

### Step 1: Create Pool and Provider

```bash
# Create the pool (one per organization or project — can be reused)
gcloud iam workload-identity-pools create github-pool \
  --location=global \
  --display-name="GitHub Actions" \
  --description="WIF pool for GitHub Actions workflows"

# Create the OIDC provider for GitHub
gcloud iam workload-identity-pools providers create-oidc github-provider \
  --location=global \
  --workload-identity-pool=github-pool \
  --issuer-uri="https://token.actions.githubusercontent.com" \
  --attribute-mapping="\
    google.subject=assertion.sub,\
    attribute.repository=assertion.repository,\
    attribute.repository_owner=assertion.repository_owner,\
    attribute.actor=assertion.actor,\
    attribute.ref=assertion.ref,\
    attribute.workflow=assertion.workflow" \
  --attribute-condition="assertion.repository_owner=='YOUR_ORG_OR_USERNAME'"
```

### Step 2: Bind SA to Pool (Per-Repo or Per-Org)

```bash
# Get the pool resource name
POOL_NAME=$(gcloud iam workload-identity-pools describe github-pool \
  --location=global \
  --format="value(name)")

# Bind: only a specific repo can impersonate this SA
gcloud iam service-accounts add-iam-policy-binding \
  deploy-sa@PROJECT.iam.gserviceaccount.com \
  --role=roles/iam.workloadIdentityUser \
  --member="principalSet://iam.googleapis.com/${POOL_NAME}/attribute.repository/YOUR_ORG/YOUR_REPO"

# Bind: any repo in the org (less restrictive)
gcloud iam service-accounts add-iam-policy-binding \
  deploy-sa@PROJECT.iam.gserviceaccount.com \
  --role=roles/iam.workloadIdentityUser \
  --member="principalSet://iam.googleapis.com/${POOL_NAME}/attribute.repository_owner/YOUR_ORG"

# Bind: only main branch of a specific repo (most restrictive)
gcloud iam service-accounts add-iam-policy-binding \
  deploy-sa@PROJECT.iam.gserviceaccount.com \
  --role=roles/iam.workloadIdentityUser \
  --member="principalSet://iam.googleapis.com/${POOL_NAME}/attribute.ref/refs/heads/main"
```

### Step 3: GitHub Actions Workflow

```yaml
name: Deploy to Cloud Run

on:
  push:
    branches: [main]

permissions:
  id-token: write   # Required for WIF token exchange
  contents: read

jobs:
  deploy:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Authenticate to GCP
        uses: google-github-actions/auth@v2
        with:
          workload_identity_provider: projects/PROJECT_NUMBER/locations/global/workloadIdentityPools/github-pool/providers/github-provider
          service_account: deploy-sa@PROJECT_ID.iam.gserviceaccount.com

      - name: Set up Cloud SDK
        uses: google-github-actions/setup-gcloud@v2

      - name: Deploy to Cloud Run
        run: |
          gcloud run deploy my-service \
            --image=REGION-docker.pkg.dev/PROJECT/REPO/IMAGE:${{ github.sha }} \
            --region=us-central1
```

## GitLab CI Setup

```bash
# Create provider for GitLab.com
gcloud iam workload-identity-pools providers create-oidc gitlab-provider \
  --location=global \
  --workload-identity-pool=gitlab-pool \
  --issuer-uri="https://gitlab.com" \
  --attribute-mapping="\
    google.subject=assertion.sub,\
    attribute.namespace_path=assertion.namespace_path,\
    attribute.project_path=assertion.project_path,\
    attribute.ref=assertion.ref,\
    attribute.ref_type=assertion.ref_type" \
  --attribute-condition="assertion.namespace_path.startsWith('YOUR_GROUP')"
```

```yaml
# .gitlab-ci.yml
deploy:
  image: google/cloud-sdk:slim
  id_tokens:
    GCP_ID_TOKEN:
      aud: https://iam.googleapis.com/projects/PROJECT_NUMBER/locations/global/workloadIdentityPools/gitlab-pool/providers/gitlab-provider
  script:
    - |
      gcloud iam workload-identity-pools create-cred-config \
        projects/PROJECT_NUMBER/locations/global/workloadIdentityPools/gitlab-pool/providers/gitlab-provider \
        --service-account=deploy-sa@PROJECT.iam.gserviceaccount.com \
        --credential-source-file=${GITLAB_CI_TOKEN_PATH} \
        --output-file=gcp-credentials.json
    - export GOOGLE_APPLICATION_CREDENTIALS=gcp-credentials.json
    - gcloud run deploy my-service ...
```

## AWS → GCP Federation

```bash
# Create AWS provider (uses AWS STS as OIDC provider)
gcloud iam workload-identity-pools providers create-aws aws-provider \
  --location=global \
  --workload-identity-pool=aws-pool \
  --account-id="AWS_ACCOUNT_ID" \
  --attribute-mapping="\
    google.subject=assertion.arn,\
    attribute.aws_role=assertion.arn.extract('assumed-role/{role}/')"

# Bind SA to specific AWS role
POOL_NAME=$(gcloud iam workload-identity-pools describe aws-pool \
  --location=global --format="value(name)")

gcloud iam service-accounts add-iam-policy-binding \
  my-sa@PROJECT.iam.gserviceaccount.com \
  --role=roles/iam.workloadIdentityUser \
  --member="principalSet://iam.googleapis.com/${POOL_NAME}/attribute.aws_role/my-lambda-role"
```

## Terraform WIF Setup

```hcl
resource "google_iam_workload_identity_pool" "github" {
  workload_identity_pool_id = "github-pool"
  display_name              = "GitHub Actions"
}

resource "google_iam_workload_identity_pool_provider" "github" {
  workload_identity_pool_id          = google_iam_workload_identity_pool.github.workload_identity_pool_id
  workload_identity_pool_provider_id = "github-provider"

  oidc {
    issuer_uri = "https://token.actions.githubusercontent.com"
  }

  attribute_mapping = {
    "google.subject"              = "assertion.sub"
    "attribute.repository"        = "assertion.repository"
    "attribute.repository_owner"  = "assertion.repository_owner"
    "attribute.ref"               = "assertion.ref"
  }

  attribute_condition = "assertion.repository_owner == 'YOUR_ORG'"
}

resource "google_service_account_iam_member" "github_deploy" {
  service_account_id = google_service_account.deploy.name
  role               = "roles/iam.workloadIdentityUser"
  member             = "principalSet://iam.googleapis.com/${google_iam_workload_identity_pool.github.name}/attribute.repository/YOUR_ORG/YOUR_REPO"
}
```

## Troubleshooting

```bash
# Check if WIF token exchange is working
# (GitHub Actions: check the 'Authenticate to GCP' step output)

# Common error: "Error 403: The caller does not have permission"
# → Check the principalSet matches the actual token claims
# → Print OIDC token claims to debug:
#   In GitHub Actions: echo $ACTIONS_ID_TOKEN_REQUEST_URL

# Common error: "attribute_condition is false"
# → Your attribute_condition expression filtered out the token
# → Temporarily remove condition for debugging, then add back

# Inspect token claims (GitHub Actions)
- name: Debug OIDC token
  run: |
    TOKEN=$(curl -s -H "Authorization: bearer $ACTIONS_ID_TOKEN_REQUEST_TOKEN" \
      "$ACTIONS_ID_TOKEN_REQUEST_URL&audience=sts.googleapis.com" | jq -r '.value')
    echo $TOKEN | cut -d. -f2 | base64 -d 2>/dev/null | python3 -m json.tool
```

## Security Best Practices

- Restrict `attribute_condition` to your org/group — never accept tokens from all issuers
- Bind SAs at the repository level (not org level) for production deployments
- Use a separate SA per deployment target (dev SA, staging SA, prod SA)
- Audit WIF token exchanges via Cloud Audit Logs: `sts.googleapis.com`
- Rotate WIF pools and providers if organization or repo structure changes
- Never set `attribute_condition=""` (empty = accept all tokens from the provider)
