# GCS (Cloud Storage) Patterns

## Bucket Configuration

```bash
# Create bucket with production-safe settings
gcloud storage buckets create gs://BUCKET_NAME \
  --location=us-central1 \
  --uniform-bucket-level-access \
  --public-access-prevention \
  --default-storage-class=STANDARD

# Enable versioning (important for critical data)
gcloud storage buckets update gs://BUCKET_NAME --versioning

# Enable soft delete (protects against accidental deletion, 7-day retention)
gcloud storage buckets update gs://BUCKET_NAME --soft-delete-duration=7d
```

## Storage Classes

| Class | Use Case | Retrieval Cost | Minimum Storage |
|-------|----------|---------------|----------------|
| STANDARD | Frequently accessed data | Free | None |
| NEARLINE | Monthly access | $0.01/GB | 30 days |
| COLDLINE | Quarterly access | $0.02/GB | 90 days |
| ARCHIVE | Annual access / long-term backups | $0.05/GB | 365 days |

## IAM vs ACLs (Always Use IAM)

```bash
# ALWAYS use uniform bucket-level access (IAM only)
gcloud storage buckets create gs://BUCKET_NAME --uniform-bucket-level-access

# Grant IAM roles (preferred over ACLs)
gcloud storage buckets add-iam-policy-binding gs://BUCKET_NAME \
  --member=serviceAccount:my-service-sa@PROJECT.iam.gserviceaccount.com \
  --role=roles/storage.objectViewer

gcloud storage buckets add-iam-policy-binding gs://BUCKET_NAME \
  --member=serviceAccount:upload-sa@PROJECT.iam.gserviceaccount.com \
  --role=roles/storage.objectCreator
```

**Role quick-ref:**

| Role | Permission |
|------|-----------|
| `roles/storage.objectViewer` | Read objects |
| `roles/storage.objectCreator` | Upload objects (no read/delete) |
| `roles/storage.objectUser` | Read + create + delete objects |
| `roles/storage.admin` | Full bucket + object control |

Never grant `roles/storage.admin` to application service accounts.

## Lifecycle Rules

```json
{
  "rule": [
    {
      "action": {"type": "SetStorageClass", "storageClass": "NEARLINE"},
      "condition": {"age": 30, "matchesStorageClass": ["STANDARD"]}
    },
    {
      "action": {"type": "SetStorageClass", "storageClass": "COLDLINE"},
      "condition": {"age": 90, "matchesStorageClass": ["NEARLINE"]}
    },
    {
      "action": {"type": "Delete"},
      "condition": {"age": 365}
    },
    {
      "action": {"type": "Delete"},
      "condition": {"isLive": false, "numNewerVersions": 3}
    }
  ]
}
```

```bash
gcloud storage buckets update gs://BUCKET_NAME --lifecycle-file=lifecycle.json
```

## Object Operations

```bash
# Upload
gcloud storage cp local-file.json gs://BUCKET_NAME/path/file.json

# Download
gcloud storage cp gs://BUCKET_NAME/path/file.json ./local-file.json

# Recursive sync (replaces gsutil rsync)
gcloud storage rsync --recursive ./local-dir/ gs://BUCKET_NAME/prefix/

# List objects with metadata
gcloud storage ls -l gs://BUCKET_NAME/path/

# Delete
gcloud storage rm gs://BUCKET_NAME/path/file.json

# Copy between buckets
gcloud storage cp gs://SOURCE_BUCKET/file.json gs://DEST_BUCKET/file.json
```

## Signed URLs (Temporary Access Without IAM)

Signed URLs grant time-limited access to objects without requiring the requester to have GCP credentials.

```python
# Python — generate a signed URL for download
from google.cloud import storage
from datetime import timedelta

def generate_signed_url(bucket_name: str, blob_name: str, expiration_minutes: int = 60) -> str:
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_name)

    url = blob.generate_signed_url(
        version="v4",
        expiration=timedelta(minutes=expiration_minutes),
        method="GET",
    )
    return url

# Generate a signed URL for upload (PUT)
def generate_upload_url(bucket_name: str, blob_name: str) -> str:
    client = storage.Client()
    blob = client.bucket(bucket_name).blob(blob_name)

    url = blob.generate_signed_url(
        version="v4",
        expiration=timedelta(minutes=15),
        method="PUT",
        content_type="application/octet-stream",
    )
    return url
```

```go
// Go — signed URL
import (
    "cloud.google.com/go/storage"
    "time"
)

func signedURL(bucket, object string) (string, error) {
    client, err := storage.NewClient(ctx)
    if err != nil {
        return "", err
    }

    opts := &storage.SignedURLOptions{
        Scheme:  storage.SigningSchemeV4,
        Method:  "GET",
        Expires: time.Now().Add(15 * time.Minute),
    }
    return client.Bucket(bucket).SignedURL(object, opts)
}
```

## CORS Configuration

Required when browser clients upload directly to GCS:

```json
[
  {
    "origin": ["https://app.example.com"],
    "method": ["GET", "PUT", "POST"],
    "responseHeader": ["Content-Type", "Content-MD5"],
    "maxAgeSeconds": 3600
  }
]
```

```bash
gcloud storage buckets update gs://BUCKET_NAME --cors-file=cors.json
```

## Bucket Naming Conventions

- **Global namespace:** bucket names are globally unique across all GCP projects.
- **Prefix with project ID** to avoid collisions: `PROJECT_ID-uploads`, `PROJECT_ID-backups`
- Avoid sensitive words in bucket names (they appear in URLs)
- All lowercase, hyphens allowed, no underscores (affects DNS compatibility)

## Anti-patterns

| Anti-pattern | Fix |
|-------------|-----|
| ACL-based access on new buckets | Use `--uniform-bucket-level-access` |
| `--no-public-access-prevention` without intent | Set `--public-access-prevention` on all private buckets |
| No lifecycle rules on log/archive buckets | Set NEARLINE/COLDLINE/Delete lifecycle |
| Storing secrets or credentials as GCS objects | Use Secret Manager |
| `roles/storage.admin` for application SAs | Use `roles/storage.objectUser` or narrower |
| Not validating content type on uploads | Validate MIME type and size in the signed URL handler |
| Using `gsutil` in new scripts | Use `gcloud storage` instead |
