# Pub/Sub Patterns

## Push vs Pull

| Dimension | Push | Pull |
|-----------|------|------|
| Delivery mechanism | Pub/Sub calls your endpoint | Your code calls Pub/Sub |
| Scaling | Automatic (tied to Pub/Sub throughput) | Controlled by your consumer |
| Auth | Pub/Sub presents OIDC token | Consumer uses ADC/SA |
| Error handling | HTTP status code signals ack/nack | Explicit `ack()` / `nack()` |
| Best for | Cloud Run, Cloud Functions (event-driven) | Workers that need flow control, batching |
| Backpressure | None — Pub/Sub pushes at full rate | Consumer controls rate |

**Use push subscriptions** when your consumer is an HTTP endpoint (Cloud Run, Cloud Functions). The Pub/Sub service scales the push rate to match your endpoint's throughput.

**Use pull subscriptions** when you need explicit flow control, message batching, or are consuming from long-running workers.

## Topic and Subscription Setup

```bash
# Create topic
gcloud pubsub topics create orders-created

# Create dead-letter topic (always set up DLT in production)
gcloud pubsub topics create orders-created-dlq

# Create pull subscription with DLT
gcloud pubsub subscriptions create orders-worker \
  --topic=orders-created \
  --ack-deadline=60 \
  --message-retention-duration=7d \
  --min-retry-delay=10s \
  --max-retry-delay=600s \
  --dead-letter-topic=orders-created-dlq \
  --max-delivery-attempts=5

# Create push subscription targeting Cloud Run
gcloud pubsub subscriptions create orders-push \
  --topic=orders-created \
  --push-endpoint=https://orders-service-HASH-uc.a.run.app/pubsub \
  --push-auth-service-account=pubsub-invoker@PROJECT.iam.gserviceaccount.com \
  --ack-deadline=60 \
  --dead-letter-topic=orders-created-dlq \
  --max-delivery-attempts=5
```

## IAM for Push Subscriptions

Pub/Sub needs permission to invoke your Cloud Run service:

```bash
# Allow Pub/Sub to invoke Cloud Run service
gcloud run services add-iam-policy-binding orders-service \
  --region=us-central1 \
  --member=serviceAccount:pubsub-invoker@PROJECT.iam.gserviceaccount.com \
  --role=roles/run.invoker

# Allow Pub/Sub to create tokens (for push auth)
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member=serviceAccount:service-PROJECT_NUMBER@gcp-sa-pubsub.iam.gserviceaccount.com \
  --role=roles/iam.serviceAccountTokenCreator
```

## Message Handler Pattern (Cloud Run / Cloud Functions)

```python
# Python — Cloud Run push endpoint
import base64
import json
from flask import Flask, request

app = Flask(__name__)

@app.route('/pubsub', methods=['POST'])
def handle_pubsub():
    envelope = request.get_json()
    if not envelope or 'message' not in envelope:
        return 'Bad Request: no Pub/Sub message', 400

    message = envelope['message']
    data = base64.b64decode(message['data']).decode('utf-8')
    attributes = message.get('attributes', {})
    message_id = message['messageId']

    try:
        payload = json.loads(data)
        process_message(payload, attributes)
        return '', 204  # ACK: return 2xx
    except Exception as e:
        # NACK: return 5xx to trigger retry
        # Return 4xx only for messages you never want retried (bad format)
        print(f"Error processing {message_id}: {e}")
        return 'Internal Server Error', 500
```

**ACK semantics:**
- Return `2xx` to acknowledge (message deleted from subscription)
- Return `5xx` to nack (Pub/Sub retries with exponential backoff up to max-delivery-attempts)
- Return `4xx` to nack but only use for messages that should never be retried (poison pills)

## Idempotency

Pub/Sub delivers **at-least-once**. Your handler must be idempotent.

Strategies:
- **Deduplication table:** Store processed `message.messageId` in Firestore/Redis with TTL
- **Upsert over insert:** Use `INSERT ... ON CONFLICT DO NOTHING` in SQL
- **Conditional writes:** Check current state before applying (e.g., check order status before marking shipped)

```python
def process_message(payload, attributes):
    message_id = attributes.get('messageId')

    # Deduplication check
    if redis_client.get(f"processed:{message_id}"):
        return  # Already processed — idempotent skip

    # Process the message
    apply_order(payload)

    # Mark as processed with TTL (7 days matches message retention)
    redis_client.setex(f"processed:{message_id}", 604800, "1")
```

## Dead-Letter Topic Handling

```bash
# Create a subscription on the DLT to monitor and reprocess failed messages
gcloud pubsub subscriptions create orders-dlq-monitor \
  --topic=orders-created-dlq \
  --ack-deadline=600

# Inspect failed messages
gcloud pubsub subscriptions pull orders-dlq-monitor --limit=10 --auto-ack=false

# Grant Pub/Sub permission to publish to DLT
gcloud pubsub topics add-iam-policy-binding orders-created-dlq \
  --member=serviceAccount:service-PROJECT_NUMBER@gcp-sa-pubsub.iam.gserviceaccount.com \
  --role=roles/pubsub.publisher
```

## Flow Control for Pull Subscribers

```python
# Python — pull subscriber with flow control
from google.cloud import pubsub_v1

subscriber = pubsub_v1.SubscriberClient()
subscription_path = subscriber.subscription_path(PROJECT, SUBSCRIPTION)

flow_control = pubsub_v1.types.FlowControl(
    max_messages=100,       # Process at most 100 messages concurrently
    max_bytes=10 * 1024 * 1024,  # 10 MB in-flight limit
)

streaming_pull_future = subscriber.subscribe(
    subscription_path,
    callback=handle_message,
    flow_control=flow_control,
)
```

## Anti-patterns

| Anti-pattern | Fix |
|-------------|-----|
| No dead-letter topic | Always configure DLT with `--max-delivery-attempts` |
| Non-idempotent handlers | Use deduplication on `message.messageId` |
| 2xx response on processing failure | Return 5xx to trigger retry |
| `allUsers` push endpoint | Require OIDC token verification on the endpoint |
| One topic for all event types | Use separate topics per event type |
| Pull subscriber without flow control | Set `FlowControl` limits to prevent memory exhaustion |
