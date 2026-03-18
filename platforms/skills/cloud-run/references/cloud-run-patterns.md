# Cloud Run Patterns

## Service Configuration Best Practices

### Concurrency and Instance Sizing

Cloud Run's default concurrency is 80 requests per instance. Tune based on your workload:

| Workload Type | Recommended Concurrency | Recommended CPU/Memory |
|---------------|------------------------|----------------------|
| CPU-bound (image processing, ML inference) | 1–4 | 2–4 CPU, 2–4 GB |
| I/O-bound (DB queries, API calls) | 80–1000 | 1 CPU, 512 MB–1 GB |
| WebSocket / streaming | 1–10 | 1 CPU, 512 MB |
| Batch processing (jobs) | N/A (one task per container) | Scale CPU/memory to task |

```bash
gcloud run deploy my-service \
  --concurrency=100 \
  --cpu=1 \
  --memory=512Mi \
  --min-instances=1 \
  --max-instances=50
```

### Min Instances and Cold Starts

- `--min-instances=0` — scale to zero when idle (cost-optimized, cold start on first request)
- `--min-instances=1` — always one instance warm (eliminates cold start, small baseline cost)
- `--min-instances=N` — handle baseline load without scaling from zero

For latency-sensitive services (APIs with SLOs), set `min-instances >= 1`.

### CPU Allocation

```bash
# CPU allocated only during request processing (default — cheaper)
gcloud run deploy my-service --no-cpu-always-allocated

# CPU allocated even between requests (required for background work, WebSockets)
gcloud run deploy my-service --cpu-always-allocated
```

## Traffic Management and Canary Releases

### Traffic Splits

```bash
# Deploy a new revision without shifting traffic
gcloud run deploy my-service --image=IMAGE:v2 --no-traffic

# Get the new revision name
NEW_REVISION=$(gcloud run revisions list --service=my-service \
  --sort-by=~createTime --limit=1 --format="value(metadata.name)")

# Gradually shift traffic (canary)
gcloud run services update-traffic my-service \
  --to-revisions="${NEW_REVISION}=10,PREVIOUS_REVISION=90"

# Promote to 100%
gcloud run services update-traffic my-service \
  --to-revisions="${NEW_REVISION}=100"

# Rollback if needed
gcloud run services update-traffic my-service \
  --to-latest=false \
  --to-revisions="PREVIOUS_REVISION=100"
```

### Tagging Revisions for Direct Access

```bash
# Tag a revision for testing before promoting
gcloud run services update-traffic my-service \
  --set-tags=canary=my-service-00005-abc

# Access the tagged revision directly at: https://canary---SERVICE_URL
```

## Secrets and Configuration

### Injecting Secrets from Secret Manager

```bash
# Mount as environment variable (latest version)
gcloud run deploy my-service \
  --set-secrets=DB_PASSWORD=db-password:latest

# Mount as file (useful for certificate bundles, JSON credentials)
gcloud run deploy my-service \
  --set-secrets=/secrets/config=app-config:1

# Multiple secrets
gcloud run deploy my-service \
  --set-secrets=DB_PASSWORD=db-password:latest,API_KEY=api-key:latest
```

### Environment Variables vs Secrets

- Environment variables: non-sensitive config (project ID, region, feature flags)
- Secret Manager: passwords, API keys, TLS certs, any sensitive value

```bash
# Environment variables (non-sensitive)
gcloud run deploy my-service \
  --set-env-vars="PROJECT_ID=my-project,LOG_LEVEL=info,ENV=production"
```

## Networking

### Private Services (Internal Ingress)

```bash
# Only reachable from VPC or other GCP services
gcloud run deploy my-service --ingress=internal

# Reachable from internal VPC + Cloud Load Balancing
gcloud run deploy my-service --ingress=internal-and-cloud-load-balancing
```

### VPC Egress (Access Private Resources)

```bash
# Route all egress through VPC (required for Cloud SQL, Memorystore, private APIs)
gcloud run deploy my-service \
  --vpc-connector=my-vpc-connector \
  --vpc-egress=all-traffic

# Route only private IP traffic through VPC (public internet goes direct)
gcloud run deploy my-service \
  --vpc-connector=my-vpc-connector \
  --vpc-egress=private-ranges-only
```

### Cloud SQL Connection (No Proxy Needed)

```bash
# Cloud Run manages the Cloud SQL Auth Proxy as a sidecar automatically
gcloud run deploy my-service \
  --add-cloudsql-instances=PROJECT:REGION:INSTANCE_NAME \
  --set-env-vars="DB_HOST=/cloudsql/PROJECT:REGION:INSTANCE_NAME,DB_NAME=mydb,DB_USER=myuser" \
  --set-secrets="DB_PASSWORD=db-password:latest"
```

## Service-to-Service Authentication

```bash
# Service A calling Service B: use ID token (not access token)
# The caller service account needs roles/run.invoker on Service B

# Go example
import "google.golang.org/api/idtoken"

audience := "https://service-b-url.run.app"
tokenSource, err := idtoken.NewTokenSource(ctx, audience)
token, err := tokenSource.Token()
req.Header.Set("Authorization", "Bearer "+token.AccessToken)
```

## Observability

```bash
# View logs for a service
gcloud logging read \
  "resource.type=cloud_run_revision AND resource.labels.service_name=my-service" \
  --limit=50 --format="table(timestamp,textPayload)"

# View request counts and latency metrics
gcloud monitoring metrics list \
  --filter="metric.type:run.googleapis.com" | grep -i request
```

## Common Anti-patterns

| Anti-pattern | Fix |
|-------------|-----|
| Storing secrets in environment variables | Use `--set-secrets` to inject from Secret Manager |
| `--allow-unauthenticated` for internal services | Use `--no-allow-unauthenticated` + IAM bindings |
| No min instances for latency-sensitive services | Set `--min-instances=1` |
| Hardcoded Cloud SQL connection strings | Use `/cloudsql/` socket path via `--add-cloudsql-instances` |
| Not pinning image tags | Use content-addressable digest (`@sha256:...`) in production |
| Using default compute SA | Always specify `--service-account` |
