# KMS Patterns (Customer-Managed Encryption Keys)

## When to Use CMEK

| Scenario | CMEK Required? |
|----------|---------------|
| Data at rest encryption (compliance: HIPAA, PCI-DSS) | Often required |
| Ability to revoke encryption instantly (data deletion SLA) | Yes |
| Audit trail for every key usage | Yes |
| Google-managed encryption is sufficient | No — default is fine |
| Regulatory requirement for customer-controlled keys | Yes |

**Default Google-managed encryption is strong.** Use CMEK only when compliance or data sovereignty requirements mandate it, or when you need the ability to instantly revoke access by disabling the key.

## Key Ring and Key Setup

```bash
# Create a key ring (regional — matches the resource region)
gcloud kms keyrings create my-keyring \
  --location=us-central1

# Create a symmetric encryption key with 90-day rotation
gcloud kms keys create my-cmek-key \
  --keyring=my-keyring \
  --location=us-central1 \
  --purpose=encryption \
  --rotation-period=7776000s \  # 90 days in seconds
  --next-rotation-time=$(date -d "+90 days" --iso-8601=seconds)

# List keys
gcloud kms keys list --keyring=my-keyring --location=us-central1

# Describe key (shows version states, rotation schedule)
gcloud kms keys describe my-cmek-key \
  --keyring=my-keyring \
  --location=us-central1
```

## CMEK for GCS Buckets

```bash
# Grant GCS service account permission to use the key
gcloud kms keys add-iam-policy-binding my-cmek-key \
  --keyring=my-keyring \
  --location=us-central1 \
  --member=serviceAccount:service-PROJECT_NUMBER@gs-project-accounts.iam.gserviceaccount.com \
  --role=roles/cloudkms.cryptoKeyEncrypterDecrypter

# Create bucket with CMEK
gcloud storage buckets create gs://my-bucket \
  --default-kms-key=projects/PROJECT/locations/us-central1/keyRings/my-keyring/cryptoKeys/my-cmek-key \
  --uniform-bucket-level-access
```

## CMEK for Cloud SQL

```bash
# Grant Cloud SQL service account permission
gcloud kms keys add-iam-policy-binding my-cmek-key \
  --keyring=my-keyring \
  --location=us-central1 \
  --member=serviceAccount:service-PROJECT_NUMBER@gcp-sa-cloud-sql.iam.gserviceaccount.com \
  --role=roles/cloudkms.cryptoKeyEncrypterDecrypter

# Create Cloud SQL instance with CMEK (must be specified at creation — cannot be added later)
gcloud sql instances create my-instance \
  --database-version=POSTGRES_16 \
  --region=us-central1 \
  --disk-encryption-key=projects/PROJECT/locations/us-central1/keyRings/my-keyring/cryptoKeys/my-cmek-key
```

## CMEK for GKE

```bash
# Grant GKE service account permission
gcloud kms keys add-iam-policy-binding my-cmek-key \
  --keyring=my-keyring \
  --location=us-central1 \
  --member=serviceAccount:service-PROJECT_NUMBER@container-engine-robot.iam.gserviceaccount.com \
  --role=roles/cloudkms.cryptoKeyEncrypterDecrypter

# Create cluster with CMEK for etcd (database-encryption)
gcloud container clusters create my-cluster \
  --region=us-central1 \
  --database-encryption-key=projects/PROJECT/locations/us-central1/keyRings/my-keyring/cryptoKeys/my-cmek-key

# Enable node disk encryption (separate from etcd)
gcloud container node-pools create my-pool \
  --cluster=my-cluster \
  --region=us-central1 \
  --disk-type=pd-ssd \
  --boot-disk-kms-key=projects/PROJECT/locations/us-central1/keyRings/my-keyring/cryptoKeys/my-cmek-key
```

## CMEK for Pub/Sub

```bash
# Grant Pub/Sub service account permission
gcloud kms keys add-iam-policy-binding my-cmek-key \
  --keyring=my-keyring \
  --location=us-central1 \
  --member=serviceAccount:service-PROJECT_NUMBER@gcp-sa-pubsub.iam.gserviceaccount.com \
  --role=roles/cloudkms.cryptoKeyEncrypterDecrypter

# Create topic with CMEK
gcloud pubsub topics create my-topic \
  --topic-encryption-key=projects/PROJECT/locations/us-central1/keyRings/my-keyring/cryptoKeys/my-cmek-key
```

## Key Rotation

Cloud KMS supports automatic key rotation — new cryptographic material is generated on schedule, but old versions remain active to decrypt existing data.

```bash
# Enable automatic rotation on existing key
gcloud kms keys update my-cmek-key \
  --keyring=my-keyring \
  --location=us-central1 \
  --rotation-period=7776000s \
  --next-rotation-time=$(date -d "+90 days" --iso-8601=seconds)

# Manual rotation: create new primary version
gcloud kms keys versions create \
  --key=my-cmek-key \
  --keyring=my-keyring \
  --location=us-central1 \
  --primary

# Disable an old key version (data encrypted with this version becomes inaccessible)
gcloud kms keys versions disable KEY_VERSION \
  --key=my-cmek-key \
  --keyring=my-keyring \
  --location=us-central1

# Destroy a key version (IRREVERSIBLE — permanently destroys cryptographic material)
gcloud kms keys versions destroy KEY_VERSION \
  --key=my-cmek-key \
  --keyring=my-keyring \
  --location=us-central1
```

**Destroying a key version permanently makes all data encrypted with that version unrecoverable.** Always disable, wait 24+ hours, verify no data recovery is needed, then destroy.

## Terraform CMEK Pattern

```hcl
resource "google_kms_key_ring" "main" {
  name     = "my-keyring"
  location = var.region
}

resource "google_kms_crypto_key" "main" {
  name            = "my-cmek-key"
  key_ring        = google_kms_key_ring.main.id
  rotation_period = "7776000s"  # 90 days

  lifecycle {
    prevent_destroy = true  # Safety — prevent accidental Terraform destroy
  }
}

resource "google_kms_crypto_key_iam_member" "gcs_encrypter" {
  crypto_key_id = google_kms_crypto_key.main.id
  role          = "roles/cloudkms.cryptoKeyEncrypterDecrypter"
  member        = "serviceAccount:service-${data.google_project.current.number}@gs-project-accounts.iam.gserviceaccount.com"
}
```

## Anti-patterns

| Anti-pattern | Fix |
|-------------|-----|
| Destroying key versions without verifying no active encrypted data | Disable → wait 7+ days → verify → destroy |
| Not enabling `prevent_destroy` in Terraform | Add `lifecycle { prevent_destroy = true }` |
| Granting `roles/cloudkms.admin` to application SAs | Use `roles/cloudkms.cryptoKeyEncrypterDecrypter` only |
| CMEK key in same project as data | Use a separate key management project for cross-project key authority |
| No key rotation schedule | Set `--rotation-period` |
| Using CMEK without audit logging | Enable Cloud KMS data access audit logs |
