# Cloud Functions 2nd Gen Patterns

## 1st Gen vs 2nd Gen

| Dimension | 1st Gen | 2nd Gen |
|-----------|---------|---------|
| Runtime | Custom runtime | Cloud Run + Eventarc |
| Max execution time | 9 minutes | 60 minutes |
| Concurrency | 1 per instance | Up to 1000 per instance |
| Min instances | Not supported | Supported |
| VPC connector | Supported | Supported |
| CPU | 1/12 to 8 vCPU | Same as Cloud Run |
| Event triggers | Pub/Sub, GCS, Firestore, HTTP | All 1st gen + Eventarc (all GCP events) |
| Recommendation | Migrate to 2nd gen | Use for new functions |

**Migrate 1st gen functions to 2nd gen** — 1st gen will eventually reach end of life.

## HTTP Functions

```python
# Python 3.12 — HTTP trigger
import functions_framework

@functions_framework.http
def handle_request(request):
    """HTTP Cloud Function."""
    request_json = request.get_json(silent=True)
    name = request_json.get('name', 'World') if request_json else 'World'
    return f'Hello, {name}!', 200
```

```go
// Go — HTTP trigger
package function

import (
    "fmt"
    "net/http"
    "cloud.google.com/go/functions/metadata"
)

func HandleRequest(w http.ResponseWriter, r *http.Request) {
    fmt.Fprintf(w, "Hello!")
}
```

## Event-Triggered Functions

### Pub/Sub Trigger

```python
# Python — Pub/Sub trigger (2nd gen)
import base64
import functions_framework
from cloudevents.http import CloudEvent

@functions_framework.cloud_event
def handle_pubsub(cloud_event: CloudEvent):
    data = base64.b64decode(cloud_event.data['message']['data']).decode()
    print(f"Received: {data}")
    # Return None (2xx) to ACK; raise exception to NACK and trigger retry
```

### GCS Trigger (via Eventarc)

```python
@functions_framework.cloud_event
def handle_gcs_event(cloud_event: CloudEvent):
    data = cloud_event.data
    bucket = data['bucket']
    name = data['name']

    if not name.endswith('.json'):
        return  # Idempotent skip for non-JSON files

    process_json_file(bucket, name)
```

## Deployment

```bash
# Deploy HTTP function
gcloud functions deploy my-function \
  --gen2 \
  --runtime=python312 \
  --region=us-central1 \
  --source=. \
  --entry-point=handle_request \
  --trigger-http \
  --no-allow-unauthenticated \
  --service-account=function-sa@PROJECT.iam.gserviceaccount.com \
  --set-secrets=DB_PASSWORD=db-password:latest \
  --min-instances=0 \
  --max-instances=100 \
  --memory=512MiB \
  --timeout=300s

# Deploy Pub/Sub-triggered function
gcloud functions deploy process-orders \
  --gen2 \
  --runtime=go122 \
  --region=us-central1 \
  --entry-point=HandleOrder \
  --trigger-topic=orders-created \
  --service-account=function-sa@PROJECT.iam.gserviceaccount.com \
  --retry  # Enable retry on failure

# Deploy GCS-triggered function (via Eventarc)
gcloud functions deploy process-uploads \
  --gen2 \
  --runtime=python312 \
  --entry-point=handle_gcs_event \
  --trigger-event-filters="type=google.cloud.storage.object.v1.finalized" \
  --trigger-event-filters="bucket=my-upload-bucket" \
  --trigger-service-account=function-sa@PROJECT.iam.gserviceaccount.com \
  --service-account=function-sa@PROJECT.iam.gserviceaccount.com
```

## Retry Semantics

Cloud Functions event-triggered functions deliver at-least-once. Design for idempotency:

```python
from google.cloud import firestore

def handle_order(cloud_event: CloudEvent):
    event_id = cloud_event['id']  # Unique per event delivery

    db = firestore.Client()
    doc_ref = db.collection('processed_events').document(event_id)

    # Idempotency check
    if doc_ref.get().exists:
        print(f"Event {event_id} already processed — skipping")
        return

    # Process
    process_order(cloud_event.data)

    # Record as processed
    doc_ref.set({'processedAt': firestore.SERVER_TIMESTAMP})
```

**Retry configuration:**
- HTTP functions: no automatic retry (caller must retry)
- Event-triggered: enable with `--retry` flag; function must return 2xx to ACK
- Pub/Sub: NACK by raising an exception; Pub/Sub retries with backoff

## Local Testing

```bash
# Install Functions Framework
pip install functions-framework

# Test HTTP function locally
functions-framework --target=handle_request --debug

# Test event-triggered function locally
functions-framework --target=handle_pubsub \
  --signature-type=cloudevent

# Send a test CloudEvent
curl -X POST http://localhost:8080 \
  -H "Content-Type: application/json" \
  -H "ce-type: google.cloud.pubsub.topic.v1.messagePublished" \
  -H "ce-source: //pubsub.googleapis.com/projects/my-project/topics/my-topic" \
  -H "ce-id: test-event-1" \
  -H "ce-specversion: 1.0" \
  -d '{"message": {"data": "aGVsbG8=", "messageId": "1234"}}'
```

## Anti-patterns

| Anti-pattern | Fix |
|-------------|-----|
| Non-idempotent event handlers | Implement deduplication using event ID |
| 2nd gen function with timeout < processing time | Increase `--timeout` up to 3600s |
| Importing heavy libraries at module level | Lazy-import inside the function handler |
| Using 1st gen `pubsub_v1` trigger for 2nd gen | Use Eventarc / CloudEvent signature |
| Not setting `--service-account` | Always use a dedicated SA per function |
| `--allow-unauthenticated` for internal functions | Use IAM invocation for internal callers |
