# Cloud SQL Patterns

## Connection Methods

### Cloud SQL Auth Proxy (Recommended for Cloud Run)

Cloud Run automatically runs a Cloud SQL Auth Proxy sidecar — no binary to install:

```bash
# Add Cloud SQL connection when deploying
gcloud run deploy my-service \
  --add-cloudsql-instances=PROJECT:REGION:INSTANCE_NAME \
  --set-env-vars="DB_HOST=/cloudsql/PROJECT:REGION:INSTANCE_NAME,DB_PORT=5432,DB_NAME=mydb,DB_USER=myuser" \
  --set-secrets="DB_PASSWORD=db-password:latest"
```

Connection string for PostgreSQL via Unix socket:
```
host=/cloudsql/PROJECT:REGION:INSTANCE_NAME user=myuser password=PASS dbname=mydb sslmode=disable
```

### Cloud SQL Go Connector (In-Process, No Sidecar)

```go
// go.mod: github.com/GoogleCloudPlatform/cloud-sql-go-connector
import (
    "database/sql"
    "github.com/GoogleCloudPlatform/cloud-sql-go-connector/postgres/pgxv5"
)

// Register the driver and create a connection pool
cleanup, err := pgxv5.RegisterDriver("cloudsql-postgres")
if err != nil {
    return err
}
defer cleanup()

db, err := sql.Open("cloudsql-postgres",
    "host=PROJECT:REGION:INSTANCE_NAME user=myuser dbname=mydb sslmode=disable",
)
db.SetMaxOpenConns(25)
db.SetMaxIdleConns(10)
db.SetConnMaxLifetime(5 * time.Minute)
```

### Cloud SQL Python Connector

```python
# pip install cloud-sql-python-connector[pg8000] psycopg2-binary sqlalchemy

from google.cloud.sql.connector import Connector
import sqlalchemy

connector = Connector()

def get_connection():
    return connector.connect(
        "PROJECT:REGION:INSTANCE_NAME",
        "pg8000",
        user="myuser",
        password="mypassword",  # use Secret Manager in production
        db="mydb",
    )

pool = sqlalchemy.create_engine(
    "postgresql+pg8000://",
    creator=get_connection,
    pool_size=5,
    max_overflow=2,
    pool_timeout=30,
    pool_recycle=1800,
)
```

## IAM Database Authentication (No Passwords)

IAM auth lets Cloud Run / GKE service accounts authenticate to Cloud SQL without passwords.

```bash
# 1. Enable IAM auth on the instance
gcloud sql instances patch INSTANCE_NAME \
  --database-flags=cloudsql.iam_authentication=on

# 2. Create IAM user (service account user)
gcloud sql users create my-service-sa@PROJECT.iam \
  --instance=INSTANCE_NAME \
  --type=cloud_iam_service_account

# 3. Grant login on the database (PostgreSQL)
# Connect as admin and run:
GRANT ALL ON DATABASE mydb TO "my-service-sa@PROJECT.iam";

# 4. Grant Cloud SQL Client IAM role
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member=serviceAccount:my-service-sa@PROJECT.iam.gserviceaccount.com \
  --role=roles/cloudsql.client
```

Connection with IAM auth (no password):
```go
// Go Connector: set useIAMAuth=true
pgxv5.RegisterDriver("cloudsql-postgres",
    cloudsqlconn.WithIAMAuthN(),
)
db, _ := sql.Open("cloudsql-postgres",
    "host=PROJECT:REGION:INSTANCE user=my-service-sa@PROJECT.iam dbname=mydb",
)
```

## Connection Pooling

Cloud Run starts multiple container instances. Without pooling limits, each instance opens N connections:

```
# Rough formula for max connections:
max_connections = max_instances × pool_size_per_instance

# With max_instances=50 and pool_size=5 → 250 connections (within Cloud SQL limits)
```

For high-concurrency Cloud Run services, consider PgBouncer (as a Cloud Run sidecar or separate service) or Cloud SQL's built-in connection pooling.

```bash
# Check current connection count
gcloud sql operations list --instance=INSTANCE_NAME \
  --filter="operationType=QUERY" --limit=5
```

## Migrations

Run migrations as a pre-deployment step, not at application startup.

```bash
# Pattern: Cloud Run Job for migrations (run before deploying the service)
gcloud run jobs create migrate-job \
  --image=REGION-docker.pkg.dev/PROJECT/REPO/IMAGE:TAG \
  --region=us-central1 \
  --service-account=migrator-sa@PROJECT.iam.gserviceaccount.com \
  --add-cloudsql-instances=PROJECT:REGION:INSTANCE_NAME \
  --set-env-vars="DB_HOST=/cloudsql/PROJECT:REGION:INSTANCE_NAME" \
  --set-secrets="DB_PASSWORD=db-password:latest" \
  --command=migrate,up

# Execute migration before deploying
gcloud run jobs execute migrate-job --region=us-central1 --wait

# Then deploy the service
gcloud run deploy my-service --image=...
```

## Read Replicas

```bash
# Create a read replica
gcloud sql instances create my-replica \
  --master-instance-name=INSTANCE_NAME \
  --region=us-central1

# Get replica connection info
gcloud sql instances describe my-replica --format="value(ipAddresses)"
```

Configure your application to route read queries to the replica:
```python
# SQLAlchemy: separate engines for write and read
write_engine = create_engine("postgresql://PRIMARY_HOST/mydb")
read_engine  = create_engine("postgresql://REPLICA_HOST/mydb")
```

## Backup and Recovery

```bash
# Enable automated backups (should be on by default in production)
gcloud sql instances patch INSTANCE_NAME \
  --backup-start-time=03:00 \
  --enable-point-in-time-recovery \
  --retained-backups-count=14 \
  --retained-transaction-log-days=7

# Manual backup
gcloud sql backups create --instance=INSTANCE_NAME

# List backups
gcloud sql backups list --instance=INSTANCE_NAME

# Restore to a point in time (creates a new instance)
gcloud sql instances clone INSTANCE_NAME NEW_INSTANCE_NAME \
  --point-in-time=2026-02-20T03:00:00.000Z
```

## Anti-patterns

| Anti-pattern | Fix |
|-------------|-----|
| Public IP without Cloud SQL Proxy | Use Private IP + Auth Proxy/Connector |
| Hardcoded DB passwords | Secret Manager + `--set-secrets` |
| No connection pool limits | Set `pool_size`, `max_overflow` |
| Running migrations at app startup | Cloud Run Job before service deploy |
| Sharing Cloud SQL instance across prod/staging | Separate instances per environment |
| `sslmode=require` without cert validation | Use Auth Proxy (handles TLS automatically) |
| No point-in-time recovery | Enable PITR in production |
