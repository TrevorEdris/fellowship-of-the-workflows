---
name: gcp-data
description: "Design and operate GCP data stores: Cloud SQL (MySQL/PostgreSQL/SQLServer), Firestore, Cloud Storage (GCS), Spanner, Bigtable, Memorystore (Redis/Valkey), and AlloyDB. Includes connection patterns, data modeling, and managed MCP server setup."
context: fork
allowed-tools: Bash, Read, Glob, Grep, Write
model: sonnet
argument-hint: "[select|cloud-sql|firestore|gcs|spanner|bigtable|memorystore|alloydb|mcp]"
tags: [gcp, architecture]
---

# GCP Data

Design schemas, configure connections, and operate GCP-managed data stores.

---

## When to Use

- Selecting the right GCP database for your use case
- Configuring Cloud SQL connections via Auth Proxy or Cloud SQL Connector
- Designing Firestore data models and security rules
- Setting up GCS buckets with correct IAM, lifecycle, and CORS
- Working with Spanner schema design or read/write transactions
- Configuring Memorystore (Redis/Valkey) for caching
- Setting up managed MCP servers for database AI agent access

---

## Quick Start

```
/gcp-data select       # Decision tree: which database for your use case
/gcp-data cloud-sql    # Cloud SQL connection, IAM auth, migrations
/gcp-data firestore    # Firestore data modeling and security rules
/gcp-data gcs          # GCS bucket setup, IAM, lifecycle, signed URLs
/gcp-data spanner      # Spanner schema design and transaction patterns
/gcp-data bigtable     # Bigtable schema design and row key patterns
/gcp-data memorystore  # Memorystore Redis/Valkey configuration
/gcp-data alloydb      # AlloyDB connection and vector search setup
/gcp-data mcp          # Managed MCP server setup for database AI access
```

---

## Context

ACTIVE PROJECT:
```
!`gcloud config get-value project 2>/dev/null || echo "no active project"`
```

CLOUD SQL INSTANCES:
```
!`gcloud sql instances list --format="table(name,databaseVersion,state,ipAddresses[0].ipAddress)" 2>/dev/null || echo "unable to list"`
```

GCS BUCKETS:
```
!`gcloud storage buckets list --format="value(name)" 2>/dev/null | head -10 || echo "none"`
```

FIRESTORE DATABASE:
```
!`gcloud firestore databases list --format="table(name,type,locationId)" 2>/dev/null || echo "none"`
```

---

## Mode: select

**Database selection decision tree:**

| Requirement | Recommended Service |
|-------------|-------------------|
| Relational, existing SQL app, <10TB | **Cloud SQL** (PostgreSQL preferred) |
| Relational, planet-scale, multi-region | **Spanner** |
| Relational, PostgreSQL-compatible, ML/vector | **AlloyDB** |
| Document, serverless, real-time sync | **Firestore** |
| Wide-column, time-series, analytics, >1PB | **Bigtable** |
| Object storage, files, blobs, static hosting | **Cloud Storage (GCS)** |
| Cache, session store, queue | **Memorystore** (Redis or Valkey) |
| App Engine legacy | Cloud Datastore (Firestore in Datastore mode) |

**Anti-patterns:**
- Cloud SQL for global writes (use Spanner)
- Spanner for < 1TB relational data (cost-prohibitive; use Cloud SQL)
- Firestore for analytics queries (use BigQuery export)
- Bigtable for OLTP (no transactions, no secondary indexes)

See `references/database-selection.md` for the full decision matrix with cost and scaling guidance.

---

## Mode: cloud-sql

Configure Cloud SQL with secure, scalable connection patterns.

### Create Instance

```bash
gcloud sql instances create INSTANCE_NAME \
  --database-version=POSTGRES_16 \
  --region=REGION \
  --tier=db-g1-small \
  --storage-type=SSD \
  --storage-auto-increase \
  --backup-start-time=03:00 \
  --enable-point-in-time-recovery \
  --deletion-protection
```

### Connection: Cloud SQL Auth Proxy (preferred for Cloud Run)

Cloud Run automatically gets Cloud SQL connections via the Cloud SQL Auth Proxy sidecar — no proxy binary needed:

```bash
gcloud run deploy SERVICE_NAME \
  --add-cloudsql-instances=PROJECT:REGION:INSTANCE_NAME \
  --set-env-vars="DB_HOST=/cloudsql/PROJECT:REGION:INSTANCE_NAME"
```

### Connection: Cloud SQL Connector (in-process, Go/Python/Java/Node.js)

```go
// Go — github.com/GoogleCloudPlatform/cloud-sql-go-connector
import "github.com/GoogleCloudPlatform/cloud-sql-go-connector/postgres/pgxv5"

cleanup, err := pgxv5.RegisterDriver("cloudsql-postgres")
db, err := sql.Open("cloudsql-postgres", "host=PROJECT:REGION:INSTANCE_NAME user=USER dbname=DB")
```

### IAM Database Authentication

```bash
# Create a service account user
gcloud sql users create SA@PROJECT.iam \
  --instance=INSTANCE_NAME \
  --type=cloud_iam_service_account

# Grant Cloud SQL Client role
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member=serviceAccount:SA@PROJECT.iam.gserviceaccount.com \
  --role=roles/cloudsql.client
```

**Anti-patterns:**
- Public IP without Authorized Networks or Cloud SQL Proxy
- Hardcoded DB passwords (use Secret Manager)
- Opening Cloud SQL to `0.0.0.0/0`

See `references/cloud-sql-patterns.md` for connection pooling, migrations, and read replicas.

---

## Mode: firestore

Design Firestore data models and configure security rules.

### Data Modeling Principles

- **Denormalize aggressively.** Joins don't exist — embed related data or duplicate it.
- **Design for your query patterns.** Collection structure should match access patterns, not normalize data.
- **Subcollection vs array.** Use subcollections for unbounded lists (messages, orders). Use arrays for bounded, co-read data.
- **Avoid large documents.** >1MB triggers per-read bottlenecks; aim for <100KB per document.

```
users/{userId}
  orders/{orderId}        ← subcollection: unbounded
  profile                 ← embedded: read together with user
  recentOrderIds: [...]   ← array: bounded, co-read
```

### Queries

```python
# Python — query with compound index
from google.cloud import firestore

db = firestore.Client()
orders = (
    db.collection("orders")
    .where("userId", "==", user_id)
    .where("status", "==", "pending")
    .order_by("createdAt", direction=firestore.Query.DESCENDING)
    .limit(10)
    .stream()
)
```

**Composite indexes required** for queries that filter on multiple fields or sort + filter. Create in `firestore.indexes.json`.

### Security Rules

```
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    match /users/{userId} {
      allow read, write: if request.auth != null && request.auth.uid == userId;
    }
    match /orders/{orderId} {
      allow read: if request.auth != null && resource.data.userId == request.auth.uid;
      allow create: if request.auth != null && request.resource.data.userId == request.auth.uid;
    }
  }
}
```

See `references/firestore-patterns.md` for transaction patterns, batch writes, and real-time listeners.

---

## Mode: gcs

Configure Cloud Storage buckets with correct IAM, lifecycle, and CORS.

```bash
# Create bucket with uniform access (recommended — no legacy ACLs)
gcloud storage buckets create gs://BUCKET_NAME \
  --location=REGION \
  --uniform-bucket-level-access \
  --public-access-prevention

# Set lifecycle rule to delete objects after 90 days
gcloud storage buckets update gs://BUCKET_NAME \
  --lifecycle-file=lifecycle.json
```

**Lifecycle rule example:**
```json
{
  "rule": [{
    "action": {"type": "Delete"},
    "condition": {"age": 90}
  }]
}
```

### IAM vs ACLs

- Use **uniform bucket-level access** (IAM only) for all new buckets.
- ACLs are legacy and incompatible with uniform access.

### Signed URLs (temporary access without IAM)

```python
from google.cloud import storage
from datetime import timedelta

client = storage.Client()
blob = client.bucket("BUCKET").blob("path/to/object")
url = blob.generate_signed_url(expiration=timedelta(hours=1), method="GET")
```

See `references/gcs-patterns.md` for CORS config, requester pays, object versioning, and HMAC keys.

---

## Mode: spanner

Design Spanner schemas and write correct transactions.

### Schema Design Rules

- **Interleave child tables** in parent to co-locate related data.
- **Avoid hotspot row keys** — never prefix with monotonic IDs or timestamps.
- **Use UUIDs or hash-prefix** for row keys.

```sql
CREATE TABLE Users (
  UserId STRING(36) NOT NULL,
  Name STRING(MAX),
  CreatedAt TIMESTAMP NOT NULL OPTIONS (allow_commit_timestamp=true),
) PRIMARY KEY (UserId);

CREATE TABLE Orders (
  UserId STRING(36) NOT NULL,
  OrderId STRING(36) NOT NULL,
  TotalAmount NUMERIC,
) PRIMARY KEY (UserId, OrderId),
  INTERLEAVE IN PARENT Users ON DELETE CASCADE;
```

### Transactions

```go
// Read-write transaction (serializable)
_, err = client.ReadWriteTransaction(ctx, func(ctx context.Context, txn *spanner.ReadWriteTransaction) error {
    row, err := txn.ReadRow(ctx, "Users", spanner.Key{userID}, []string{"Balance"})
    // ... modify and buffer mutations
    txn.BufferWrite([]*spanner.Mutation{
        spanner.Update("Users", []string{"UserId", "Balance"}, []interface{}{userID, newBalance}),
    })
    return nil
})
```

See `references/spanner-patterns.md` for secondary indexes, mutations vs DML, and backup/restore.

---

## Mode: memorystore

Configure Memorystore for Redis or Valkey caching.

```bash
# Create a Redis instance
gcloud redis instances create INSTANCE_NAME \
  --size=1 \
  --region=REGION \
  --redis-version=redis_7_0 \
  --tier=standard

# Get connection info
gcloud redis instances describe INSTANCE_NAME --region=REGION
```

**Memorystore is VPC-only** — Cloud Run services must use a Serverless VPC Access connector to reach it.

---

## Mode: mcp

Set up managed MCP servers for AI agent database access.

### Official Google-Managed Database MCPs

| Service | Status | Auth |
|---------|--------|------|
| Cloud SQL | Preview | IAM (no key files) |
| AlloyDB | Preview | IAM (no key files) |
| Spanner | Preview | IAM (no key files) |
| Bigtable | Preview | IAM (no key files) |

Enable from Cloud Console: **AI → MCP Servers → Enable for [service]**.

Create a dedicated read-only MCP service account:
```bash
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member=serviceAccount:mcp-db-agent@PROJECT.iam.gserviceaccount.com \
  --role=roles/cloudsql.viewer  # read-only
```

See `references/mcp-database-servers.md` for full setup, capability details, and security hardening.

---

## Verification Checklist

- [ ] Database uses a dedicated service account with least-privilege roles
- [ ] Cloud SQL connections use Auth Proxy or Cloud SQL Connector (no direct public IP)
- [ ] Database passwords stored in Secret Manager
- [ ] Firestore security rules deploy and pass emulator tests
- [ ] GCS buckets use uniform bucket-level access (no ACLs)
- [ ] GCS buckets have `--public-access-prevention` unless intentionally public
- [ ] Lifecycle rules configured for transient data
- [ ] Spanner row keys don't create hotspots (no sequential prefixes)
- [ ] Memorystore accessible only via VPC (Serverless VPC Access for Cloud Run)
- [ ] MCP service account is read-only

---

## References

- `references/database-selection.md` — Decision tree with cost and scaling guidance
- `references/cloud-sql-patterns.md` — Connection pooling, IAM auth, migrations, read replicas
- `references/firestore-patterns.md` — Data modeling, subcollections, transactions, security rules
- `references/gcs-patterns.md` — Bucket naming, IAM vs ACLs, signed URLs, lifecycle, CORS
- `references/spanner-patterns.md` — Schema design, interleaved tables, transactions, mutations
- `references/mcp-database-servers.md` — Managed MCP server setup and security
