# GCP New Project Setup Checklist

Use this checklist when bootstrapping a new GCP project for production workloads.

## 1. Project and Billing

- [ ] Create project with a consistent naming convention: `ORG-SERVICE-ENV` (e.g., `acme-payments-prod`)
- [ ] Link to the correct billing account
- [ ] Set up a billing budget alert (e.g., 80% of expected monthly spend)
- [ ] Add project to the correct folder in the resource hierarchy (org → folder → project)
- [ ] Set required labels: `team`, `env`, `cost-center`

```bash
gcloud projects create acme-payments-prod \
  --name="Payments Service (Prod)" \
  --folder=FOLDER_ID

gcloud billing projects link acme-payments-prod \
  --billing-account=BILLING_ACCOUNT_ID

# Label the project
gcloud resource-manager tags bindings create \
  --tag-value=projects/acme-org/tagKeys/team/tagValues/payments \
  --parent=//cloudresourcemanager.googleapis.com/projects/acme-payments-prod
```

## 2. Enable Required APIs

Always enable APIs before creating resources. These are the baseline for most backend services:

```bash
gcloud services enable \
  cloudresourcemanager.googleapis.com \
  iam.googleapis.com \
  iamcredentials.googleapis.com \
  sts.googleapis.com \
  secretmanager.googleapis.com \
  cloudkms.googleapis.com \
  logging.googleapis.com \
  monitoring.googleapis.com \
  cloudtrace.googleapis.com \
  --project=PROJECT_ID
```

Enable service-specific APIs as needed:

```bash
# Cloud Run / Functions
gcloud services enable run.googleapis.com cloudfunctions.googleapis.com eventarc.googleapis.com

# CI/CD
gcloud services enable cloudbuild.googleapis.com artifactregistry.googleapis.com clouddeploy.googleapis.com

# Data
gcloud services enable sqladmin.googleapis.com firestore.googleapis.com storage.googleapis.com
```

## 3. IAM Hardening

- [ ] Disable the default compute service account or strip its roles
- [ ] Apply org policy to prevent SA key creation
- [ ] Remove primitive roles (Owner/Editor) from the project IAM policy where possible
- [ ] Enable the `iam.googleapis.com` Audit Log for `DATA_READ`, `DATA_WRITE`, and `ADMIN_READ`

```bash
# Disable key creation
gcloud resource-manager org-policies set-policy \
  --project=PROJECT_ID \
  iam-disable-sa-key.yaml

# Enable audit logs for IAM
gcloud projects get-iam-policy PROJECT_ID --format=json > policy.json
# Add auditConfig block for iam.googleapis.com covering DATA_READ, DATA_WRITE, ADMIN_READ
gcloud projects set-iam-policy PROJECT_ID policy.json
```

## 4. Default Service Account

The Compute Engine default service account (`PROJECT_NUMBER-compute@developer.gserviceaccount.com`) has broad Editor-equivalent scope by default. Mitigate this:

```bash
# Option A: Disable the default SA (recommended for greenfield projects)
gcloud iam service-accounts disable \
  PROJECT_NUMBER-compute@developer.gserviceaccount.com

# Option B: Remove the Editor binding and bind least-privilege roles instead
gcloud projects remove-iam-policy-binding PROJECT_ID \
  --member=serviceAccount:PROJECT_NUMBER-compute@developer.gserviceaccount.com \
  --role=roles/editor
```

## 5. Logging and Monitoring

- [ ] Enable Cloud Logging data access audit logs
- [ ] Create a log sink to a GCS bucket or BigQuery for retention beyond the 30-day default
- [ ] Set up an uptime check for the primary service endpoint
- [ ] Configure a billing anomaly alert in Cloud Monitoring

```bash
# Create a log sink for long-term retention
gcloud logging sinks create prod-audit-sink \
  storage.googleapis.com/AUDIT_BUCKET_NAME \
  --log-filter='logName:"cloudaudit.googleapis.com"' \
  --project=PROJECT_ID
```

## 6. Artifact Registry

Create a container registry before deploying Cloud Run services:

```bash
gcloud artifacts repositories create containers \
  --repository-format=docker \
  --location=REGION \
  --description="Container images for PROJECT_ID"

# Grant Cloud Build write access
gcloud artifacts repositories add-iam-policy-binding containers \
  --location=REGION \
  --member=serviceAccount:PROJECT_NUMBER@cloudbuild.gserviceaccount.com \
  --role=roles/artifactregistry.writer
```

## 7. Terraform State Bucket (if using Terraform)

```bash
gcloud storage buckets create gs://PROJECT_ID-terraform-state \
  --location=US \
  --uniform-bucket-level-access \
  --public-access-prevention

gcloud storage buckets update gs://PROJECT_ID-terraform-state \
  --versioning
```

## Post-Setup Verification

```bash
# Verify: no user-managed SA keys exist
gcloud iam service-accounts list --format="value(email)" | \
  xargs -I{} gcloud iam service-accounts keys list \
    --iam-account={} --managed-by=user --format="value(name)" 2>/dev/null

# Verify: no allUsers or allAuthenticatedUsers in project IAM
gcloud projects get-iam-policy PROJECT_ID \
  --flatten="bindings[].members" \
  --filter="bindings.members:(allUsers OR allAuthenticatedUsers)"

# Verify: required APIs are enabled
gcloud services list --enabled --filter="name:(run.googleapis.com OR iam.googleapis.com OR secretmanager.googleapis.com)"
```
