---
name: cloud-run
description: "Deploy and operate Cloud Run services/jobs, Cloud Functions 2nd gen, Eventarc triggers, Pub/Sub topics/subscriptions, Cloud Tasks queues, and Cloud Scheduler jobs. Use for GCP serverless compute and async messaging workflows."
context: fork
agent: cloud-run-specialist
allowed-tools: Bash, Read, Glob, Grep, Write
model: sonnet
argument-hint: "[deploy|jobs|functions|pubsub|eventarc|tasks|scheduler|decide]"
tags: [gcp, infrastructure]
---

# Cloud Run

Deploy, configure, and operate GCP serverless compute and async messaging services.

---

## When to Use

- Deploying a containerized service or job to Cloud Run
- Configuring Cloud Functions 2nd gen (which runs on Cloud Run + Eventarc)
- Setting up Pub/Sub topics, subscriptions, push endpoints, or dead-letter topics
- Routing events via Eventarc (Cloud Audit Logs, GCS events, custom events)
- Queueing work with Cloud Tasks or scheduling with Cloud Scheduler
- Choosing between Cloud Run, Cloud Functions, and GKE

---

## Quick Start

```
/cloud-run deploy      # Deploy a service or update an existing one
/cloud-run jobs        # Create/run a Cloud Run job (batch, one-shot)
/cloud-run functions   # Deploy a Cloud Function (2nd gen)
/cloud-run pubsub      # Set up Pub/Sub topics, subscriptions, DLT
/cloud-run eventarc    # Configure Eventarc triggers
/cloud-run tasks       # Create Cloud Tasks queues and enqueue tasks
/cloud-run scheduler   # Configure Cloud Scheduler cron jobs
/cloud-run decide      # Decision tree: Cloud Run vs Functions vs GKE
```

---

## Context

ACTIVE PROJECT:
```
!`gcloud config get-value project 2>/dev/null || echo "no active project"`
```

DEPLOYED CLOUD RUN SERVICES:
```
!`gcloud run services list --format="table(metadata.name,status.url,status.conditions[0].status)" 2>/dev/null || echo "unable to list services"`
```

DEPLOYED CLOUD FUNCTIONS:
```
!`gcloud functions list --gen2 --format="table(name,state,serviceConfig.uri)" 2>/dev/null || echo "unable to list functions"`
```

PUB/SUB TOPICS:
```
!`gcloud pubsub topics list --format="value(name)" 2>/dev/null | head -10 || echo "none"`
```

---

## Mode: decide

**Cloud Run vs Cloud Functions vs GKE — decision tree:**

| Requirement | Recommendation |
|-------------|---------------|
| Containerized HTTP service | **Cloud Run** |
| Event-driven, short-lived function | **Cloud Functions 2nd gen** |
| Existing Kubernetes workloads | **GKE** |
| Job that runs to completion (batch) | **Cloud Run Jobs** |
| GPU workload | **Cloud Run** (GPU support) or **GKE** |
| VPC-native networking required | Cloud Run (VPC egress) or **GKE** |
| Multi-container pods | **GKE** |
| >1h execution time | **Cloud Run Jobs** or **GKE** |

Cloud Functions 2nd gen deploys as Cloud Run services under the hood — they share the same runtime model. Choose Functions when the function-as-unit-of-code abstraction is preferred; choose Cloud Run when you control the container.

See `references/serverless-decision-tree.md` for full comparison.

---

## Mode: deploy

Deploy or update a Cloud Run service.

**Steps:**
1. Verify the image is in Artifact Registry:
   ```bash
   gcloud artifacts repositories list
   ```
2. Deploy the service:
   ```bash
   gcloud run deploy SERVICE_NAME \
     --image=REGION-docker.pkg.dev/PROJECT/REPO/IMAGE:TAG \
     --region=REGION \
     --service-account=SERVICE_SA@PROJECT.iam.gserviceaccount.com \
     --set-secrets=DB_PASS=db-password:latest \
     --min-instances=1 \
     --max-instances=100 \
     --concurrency=80 \
     --cpu=1 \
     --memory=512Mi \
     --no-allow-unauthenticated
   ```
3. Verify deployment health:
   ```bash
   gcloud run services describe SERVICE_NAME --region=REGION
   ```
4. Run smoke test against the service URL.

**Key flags:**
- `--no-allow-unauthenticated` — require IAM auth (default for internal services)
- `--ingress=internal` — restrict to VPC only
- `--vpc-connector=CONNECTOR` — route egress through VPC
- `--set-secrets=ENV_VAR=SECRET_NAME:VERSION` — inject from Secret Manager
- `--min-instances=1` — eliminate cold starts for latency-sensitive services

See `references/cloud-run-patterns.md` for traffic splits, canary rollouts, and revision pinning.
See `assets/cloud-run-service.yaml` for declarative service YAML.

---

## Mode: jobs

Run batch workloads or one-shot tasks with Cloud Run Jobs.

```bash
# Create a job
gcloud run jobs create JOB_NAME \
  --image=REGION-docker.pkg.dev/PROJECT/REPO/IMAGE:TAG \
  --region=REGION \
  --service-account=JOB_SA@PROJECT.iam.gserviceaccount.com \
  --set-secrets=DB_PASS=db-password:latest \
  --tasks=10 \
  --max-retries=3 \
  --task-timeout=3600s

# Execute the job
gcloud run jobs execute JOB_NAME --region=REGION

# Execute and wait for completion
gcloud run jobs execute JOB_NAME --region=REGION --wait
```

**Use `CLOUD_RUN_TASK_INDEX`** env var to split work across tasks (0 to N-1).

---

## Mode: functions

Deploy Cloud Functions 2nd gen (Eventarc + Cloud Run backend).

```bash
# HTTP function
gcloud functions deploy FUNCTION_NAME \
  --gen2 \
  --runtime=go122 \
  --region=REGION \
  --source=. \
  --entry-point=HandleRequest \
  --trigger-http \
  --no-allow-unauthenticated \
  --service-account=FUNCTION_SA@PROJECT.iam.gserviceaccount.com

# Pub/Sub triggered function
gcloud functions deploy FUNCTION_NAME \
  --gen2 \
  --runtime=python312 \
  --trigger-topic=MY_TOPIC \
  --entry-point=handle_pubsub
```

**Idempotency is mandatory** for event-triggered functions — Pub/Sub and Eventarc deliver at-least-once.

See `references/cloud-functions-patterns.md` for retry semantics, timeout config, and local testing.

---

## Mode: pubsub

Configure Pub/Sub for async messaging.

```bash
# Create topic and subscription
gcloud pubsub topics create MY_TOPIC
gcloud pubsub subscriptions create MY_SUB \
  --topic=MY_TOPIC \
  --ack-deadline=60 \
  --message-retention-duration=7d \
  --dead-letter-topic=MY_TOPIC-dlq \
  --max-delivery-attempts=5

# Push subscription to Cloud Run
gcloud pubsub subscriptions create MY_PUSH_SUB \
  --topic=MY_TOPIC \
  --push-endpoint=https://SERVICE_URL/pubsub \
  --push-auth-service-account=PUBSUB_SA@PROJECT.iam.gserviceaccount.com
```

**Required IAM for push subscriptions:**
```bash
# Allow Pub/Sub to invoke Cloud Run
gcloud run services add-iam-policy-binding SERVICE_NAME \
  --member=serviceAccount:PUBSUB_SA@PROJECT.iam.gserviceaccount.com \
  --role=roles/run.invoker
```

See `references/pubsub-patterns.md` for push vs pull trade-offs, flow control, and DLT patterns.

---

## Mode: eventarc

Route GCP events to Cloud Run or Cloud Functions via Eventarc.

```bash
# Trigger on GCS object creation
gcloud eventarc triggers create MY_TRIGGER \
  --location=REGION \
  --destination-run-service=SERVICE_NAME \
  --destination-run-region=REGION \
  --event-filters="type=google.cloud.storage.object.v1.finalized" \
  --event-filters="bucket=MY_BUCKET" \
  --service-account=EVENTARC_SA@PROJECT.iam.gserviceaccount.com

# Trigger on Cloud Audit Log (e.g., BigQuery job completion)
gcloud eventarc triggers create BQ_TRIGGER \
  --event-filters="type=google.cloud.audit.log.v1.written" \
  --event-filters="serviceName=bigquery.googleapis.com" \
  --event-filters="methodName=jobservice.insert" \
  --destination-run-service=SERVICE_NAME
```

See `references/eventarc-routing.md` for event type reference, attribute filtering, and retry semantics.

---

## Mode: tasks

Queue and dispatch work with Cloud Tasks.

```bash
# Create a queue
gcloud tasks queues create MY_QUEUE \
  --location=REGION \
  --max-concurrent-dispatches=10 \
  --max-dispatches-per-second=100

# Enqueue a task (via API — Cloud Tasks requires programmatic enqueueing)
# See references/cloud-run-patterns.md for SDK examples per language
```

**When to use Cloud Tasks vs Pub/Sub:**
- Cloud Tasks: one-off work units with retry semantics, scheduling delay, rate limiting, deduplication
- Pub/Sub: fan-out messaging, multiple subscribers, high-throughput streaming

---

## Mode: scheduler

Run cron jobs targeting Cloud Run, Pub/Sub, or HTTP endpoints.

```bash
gcloud scheduler jobs create http MY_JOB \
  --location=REGION \
  --schedule="0 */6 * * *" \
  --uri=https://SERVICE_URL/cron/cleanup \
  --http-method=POST \
  --oidc-service-account-email=SCHEDULER_SA@PROJECT.iam.gserviceaccount.com \
  --oidc-token-audience=https://SERVICE_URL
```

---

## Verification Checklist

- [ ] Service deploys successfully (`gcloud run services describe`)
- [ ] Service uses a dedicated service account (not the default compute SA)
- [ ] Secrets injected from Secret Manager, not environment variables
- [ ] `--no-allow-unauthenticated` set for internal services
- [ ] Min instances configured for latency-sensitive services
- [ ] Health check endpoint returns 200
- [ ] Event-triggered functions are idempotent (test with duplicate delivery)
- [ ] Pub/Sub dead-letter topic configured
- [ ] IAM bindings verified: correct principals with least-privilege roles

---

## References

- `references/cloud-run-patterns.md` — Service config, revisions, traffic splits, min-instances
- `references/cloud-functions-patterns.md` — 1st vs 2nd gen, Eventarc triggers, idempotency
- `references/pubsub-patterns.md` — Topic/subscription design, push vs pull, DLT
- `references/eventarc-routing.md` — Event types, trigger config, audit log events
- `references/serverless-decision-tree.md` — Cloud Run vs Functions vs GKE

## Assets

- `assets/cloud-run-service.yaml` — Declarative Cloud Run service YAML
- `assets/cloudbuild-cloudrun-deploy.yaml` — Cloud Build + Cloud Deploy pipeline template
