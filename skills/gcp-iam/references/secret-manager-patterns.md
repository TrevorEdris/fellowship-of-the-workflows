# Secret Manager Patterns

## Creating and Managing Secrets

```bash
# Create a secret
echo -n "my-db-password" | gcloud secrets create db-password \
  --data-file=- \
  --replication-policy=automatic \
  --labels=app=my-service,env=prod

# Create secret from file
gcloud secrets create tls-cert \
  --data-file=./cert.pem \
  --replication-policy=automatic

# Create secret with regional replication (for data residency)
gcloud secrets create api-key \
  --replication-policy=user-managed \
  --locations=us-central1,us-east1

# Add a new version (rotation)
echo -n "new-password-value" | gcloud secrets versions add db-password --data-file=-

# Access the latest version
gcloud secrets versions access latest --secret=db-password

# Access a specific version
gcloud secrets versions access 3 --secret=db-password

# List versions
gcloud secrets versions list db-password

# Disable an old version (does not delete; blocks access)
gcloud secrets versions disable 1 --secret=db-password

# Destroy a version (irreversible)
gcloud secrets versions destroy 1 --secret=db-password
```

## IAM Access Control

Grant access at the secret level, not the project level.

```bash
# Grant read access to a service account
gcloud secrets add-iam-policy-binding db-password \
  --member=serviceAccount:my-service-sa@PROJECT.iam.gserviceaccount.com \
  --role=roles/secretmanager.secretAccessor

# Grant access to a specific user (emergency access)
gcloud secrets add-iam-policy-binding db-password \
  --member=user:oncall-engineer@example.com \
  --role=roles/secretmanager.secretAccessor

# Audit: who can access this secret
gcloud secrets get-iam-policy db-password

# Roles for Secret Manager
# roles/secretmanager.admin          → Full control of secrets
# roles/secretmanager.secretAccessor → Read secret values (accessor)
# roles/secretmanager.viewer         → View metadata only, not values
```

## Injecting Secrets into Cloud Run

**Preferred method: environment variable via `--set-secrets`**

```bash
# Inject secret as environment variable (no code change required)
gcloud run deploy my-service \
  --set-secrets=DB_PASSWORD=db-password:latest,API_KEY=api-key:2
```

**File mount (for certificates, JSON configs):**

```bash
# Mount secret as a file at /secrets/config
gcloud run deploy my-service \
  --set-secrets=/secrets/db-config=db-config-json:latest
```

**Programmatic access (when dynamic secret access needed):**

```python
# Python — access Secret Manager at runtime
from google.cloud import secretmanager

def get_secret(project_id: str, secret_id: str, version: str = "latest") -> str:
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{project_id}/secrets/{secret_id}/versions/{version}"
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode("utf-8")
```

```go
// Go — access at runtime
import secretmanager "cloud.google.com/go/secretmanager/apiv1"

func getSecret(ctx context.Context, projectID, secretID string) (string, error) {
    client, err := secretmanager.NewClient(ctx)
    if err != nil {
        return "", err
    }
    defer client.Close()

    name := fmt.Sprintf("projects/%s/secrets/%s/versions/latest", projectID, secretID)
    result, err := client.AccessSecretVersion(ctx, &secretmanagerpb.AccessSecretVersionRequest{
        Name: name,
    })
    if err != nil {
        return "", err
    }
    return string(result.Payload.Data), nil
}
```

## Rotation

Manual rotation pattern:

```bash
# 1. Create new version with new value
echo -n "new-rotated-value" | gcloud secrets versions add db-password --data-file=-

# 2. Update the password in the actual database/service
# 3. Verify the application works with the new version
# 4. Disable the old version
gcloud secrets versions disable OLD_VERSION_NUMBER --secret=db-password
```

Automated rotation with Cloud Functions:

```bash
# Create a Pub/Sub topic for rotation notifications
gcloud pubsub topics create secret-rotation

# Set up automatic rotation notification
gcloud secrets update db-password \
  --rotation-period=2592000s \  # 30 days
  --next-rotation-time=$(date -d "+30 days" --iso-8601)
  --topics=projects/PROJECT/topics/secret-rotation

# Deploy a Cloud Function to handle rotation notifications
# (Function receives CloudEvent on secret rotation, creates new version, updates downstream)
```

## Audit Logging

Enable Data Access audit logs for Secret Manager:

```bash
# Check if audit logging is enabled
gcloud projects get-iam-policy PROJECT_ID --format=json | \
  python3 -c "import json,sys; p=json.load(sys.stdin); print([a for a in p.get('auditConfigs',[]) if 'secretmanager' in a.get('service','')])"

# Query access logs (who accessed which secret)
gcloud logging read \
  "resource.type=audited_resource \
   AND protoPayload.serviceName=secretmanager.googleapis.com \
   AND protoPayload.methodName=AccessSecretVersion" \
  --limit=20 \
  --format="table(timestamp,protoPayload.authenticationInfo.principalEmail,protoPayload.resourceName)"
```

## Cross-Project Secret Access

```bash
# Grant access from Project B to a secret in Project A
gcloud secrets add-iam-policy-binding my-secret \
  --project=PROJECT_A \
  --member=serviceAccount:sa@PROJECT_B.iam.gserviceaccount.com \
  --role=roles/secretmanager.secretAccessor
```

Note: The service account requesting access must be from the same organization for this to work with VPC Service Controls.

## Anti-patterns

| Anti-pattern | Fix |
|-------------|-----|
| Secrets in environment variables (raw values) | Use `--set-secrets` to inject from Secret Manager |
| Secrets in Docker images or source control | Audit with `git log -p` and rotate immediately |
| Project-level `secretmanager.secretAccessor` | Bind at the secret level |
| Never rotating secrets | Set `--rotation-period`, automate version creation |
| Destroying secret versions before confirming rotation | Disable then wait 7+ days; destroy only after confirmation |
| Accessing secrets programmatically when `--set-secrets` suffices | Prefer `--set-secrets` (no SDK dependency, no network call on startup) |
| Logging secret values | Ensure handlers never log `payload.data` |
