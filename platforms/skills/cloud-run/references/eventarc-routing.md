# Eventarc Routing

## Event Source Types

| Source | Event Type Prefix | Example Use Case |
|--------|------------------|-----------------|
| Cloud Storage | `google.cloud.storage.object.v1.*` | Process uploaded files |
| Cloud Pub/Sub | `google.cloud.pubsub.topic.v1.messagePublished` | Fan-out from Pub/Sub |
| Cloud Audit Logs | `google.cloud.audit.log.v1.written` | React to any GCP API call |
| Firebase / Firestore | `google.cloud.firestore.document.v1.*` | React to DB changes |
| Cloud Build | `google.cloud.cloudbuild.build.v1.statusChanged` | Post-build automation |
| Custom (HTTP) | Custom type | Application-level events |

## Trigger Configuration

### GCS Object Events

```bash
# Trigger on any object creation in a bucket
gcloud eventarc triggers create process-uploads \
  --location=us-central1 \
  --destination-run-service=upload-processor \
  --destination-run-region=us-central1 \
  --event-filters="type=google.cloud.storage.object.v1.finalized" \
  --event-filters="bucket=my-upload-bucket" \
  --service-account=eventarc-sa@PROJECT.iam.gserviceaccount.com

# Available GCS event types:
# google.cloud.storage.object.v1.finalized   — object created/overwritten
# google.cloud.storage.object.v1.deleted     — object deleted
# google.cloud.storage.object.v1.archived    — object archived (versioned bucket)
# google.cloud.storage.object.v1.metadataUpdated — metadata changed
```

### Cloud Audit Log Events

```bash
# Trigger on any Cloud SQL instance creation
gcloud eventarc triggers create sql-instance-created \
  --location=us-central1 \
  --destination-run-service=infra-notifier \
  --destination-run-region=us-central1 \
  --event-filters="type=google.cloud.audit.log.v1.written" \
  --event-filters="serviceName=sqladmin.googleapis.com" \
  --event-filters="methodName=sql.instances.insert" \
  --service-account=eventarc-sa@PROJECT.iam.gserviceaccount.com

# Trigger on IAM policy changes (security monitoring)
gcloud eventarc triggers create iam-policy-change \
  --event-filters="type=google.cloud.audit.log.v1.written" \
  --event-filters="serviceName=cloudresourcemanager.googleapis.com" \
  --event-filters="methodName=SetIamPolicy" \
  --destination-run-service=security-monitor
```

### Pub/Sub as Eventarc Source

```bash
# Trigger Cloud Run from Pub/Sub via Eventarc (alternative to push subscription)
gcloud eventarc triggers create pubsub-to-cloud-run \
  --location=us-central1 \
  --destination-run-service=my-service \
  --destination-run-region=us-central1 \
  --event-filters="type=google.cloud.pubsub.topic.v1.messagePublished" \
  --transport-topic=my-existing-topic \
  --service-account=eventarc-sa@PROJECT.iam.gserviceaccount.com
```

## IAM Requirements for Eventarc

```bash
# Eventarc service account must have roles/run.invoker on destination service
gcloud run services add-iam-policy-binding DESTINATION_SERVICE \
  --region=us-central1 \
  --member=serviceAccount:eventarc-sa@PROJECT.iam.gserviceaccount.com \
  --role=roles/run.invoker

# For Audit Log triggers: Eventarc must be able to read audit logs
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member=serviceAccount:eventarc-sa@PROJECT.iam.gserviceaccount.com \
  --role=roles/eventarc.eventReceiver

# For GCS triggers: GCS service account must publish to Pub/Sub
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member=serviceAccount:service-PROJECT_NUMBER@gs-project-accounts.iam.gserviceaccount.com \
  --role=roles/pubsub.publisher
```

## Event Payload Structure

Events are delivered as CloudEvents (CNCF standard). Your Cloud Run handler receives:

```python
# Python — CloudEvent handler
import functions_framework
from cloudevents.http import CloudEvent

@functions_framework.cloud_event
def handle_gcs_event(cloud_event: CloudEvent):
    event_type = cloud_event['type']
    # e.g., "google.cloud.storage.object.v1.finalized"

    data = cloud_event.data
    bucket = data['bucket']
    name = data['name']
    content_type = data.get('contentType', '')

    print(f"New file: gs://{bucket}/{name} ({content_type})")
```

```go
// Go — CloudEvent handler in Cloud Run
import (
    "github.com/cloudevents/sdk-go/v2/event"
    cloudevents "github.com/cloudevents/sdk-go/v2"
)

func handleEvent(ctx context.Context, e event.Event) error {
    var data struct {
        Bucket string `json:"bucket"`
        Name   string `json:"name"`
    }
    if err := e.DataAs(&data); err != nil {
        return err
    }
    log.Printf("Processing: gs://%s/%s", data.Bucket, data.Name)
    return nil
}
```

## Retry and Dead-Lettering

Eventarc delivers events with automatic retry on non-2xx responses. Configure retry behavior at the trigger:

```bash
# View trigger retry policy
gcloud eventarc triggers describe MY_TRIGGER --location=us-central1

# For Pub/Sub-backed triggers: configure DLT on the underlying subscription
gcloud pubsub subscriptions modify-config EVENTARC_SUBSCRIPTION \
  --dead-letter-topic=eventarc-dlq \
  --max-delivery-attempts=5
```

**Your handler must be idempotent** — Eventarc guarantees at-least-once delivery.

## Eventarc vs Direct Pub/Sub Push

| Dimension | Eventarc | Direct Pub/Sub Push |
|-----------|----------|---------------------|
| Setup complexity | Higher (trigger + SA + event filter) | Lower (subscription + push endpoint) |
| Event types | GCS, Audit Logs, Firebase, Pub/Sub, custom | Pub/Sub only |
| Auth | OIDC (automatic per trigger) | OIDC on push subscription |
| Best for | Reacting to GCP service events | Application-to-application messaging |
| Routing logic | Event filter attributes | Explicit topic subscription |
