# Managed MCP Database Servers

## Overview

Google operates official managed MCP servers for GCP databases. These run on Google infrastructure — no local setup, no service account key files. Authentication uses IAM (OAuth/OIDC).

## Available Database MCPs

| Service | Status | Capabilities |
|---------|--------|-------------|
| Cloud SQL | Preview | Natural language queries, schema inspection, query optimization (MySQL/PostgreSQL/SQLServer) |
| AlloyDB | Preview | Schema creation, complex query diagnosis, vector similarity search |
| Spanner | Preview | Spanner Graph queries, relational + semantic data access |
| Bigtable | Preview | Schema inspection, row key analysis |
| Firestore | Preview | Document queries, collection structure inspection |

## Enabling Official Managed MCPs

**Cloud SQL:**
```bash
# Enable via Console: Cloud SQL → Instance → AI → Enable MCP Server
# Or via CLI (preview):
gcloud beta sql instances patch INSTANCE_NAME \
  --enable-mcp-server
```

**AlloyDB / Spanner:**
```bash
# Cloud Console → AI → MCP Servers → Enable for [service]
```

## IAM for Database MCPs

Create a dedicated, read-only MCP service account — never use an admin account.

```bash
# Create dedicated MCP agent SA
gcloud iam service-accounts create mcp-db-agent \
  --display-name="MCP Database Agent" \
  --description="Read-only DB access for AI agent MCP tools"

# Cloud SQL: read-only access
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member=serviceAccount:mcp-db-agent@PROJECT.iam.gserviceaccount.com \
  --role=roles/cloudsql.viewer

# Spanner: read-only
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member=serviceAccount:mcp-db-agent@PROJECT.iam.gserviceaccount.com \
  --role=roles/spanner.databaseReader

# Firestore: read-only
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member=serviceAccount:mcp-db-agent@PROJECT.iam.gserviceaccount.com \
  --role=roles/datastore.viewer
```

## Security Hardening

| Risk | Mitigation |
|------|-----------|
| MCP agent with write access | Use `*.viewer` and `*.reader` roles only |
| MCP accessing production data | Create a separate MCP SA scoped to non-production instances; use VPC Service Controls to restrict prod |
| Query execution (Cloud SQL MCP) | Audit executed queries via Cloud Logging: `resource.type=cloudsql_database` |
| Schema exposure | Limit MCP SA to specific databases using resource-level IAM |
| Credential exposure | Never use service account key files — IAM-based auth only |

## Audit Logging for MCP Activity

```bash
# Enable Data Access audit logs for Cloud SQL
# (captures DML, DDL, and admin operations)
gcloud logging read \
  "resource.type=cloudsql_database \
   AND protoPayload.authenticationInfo.principalEmail=mcp-db-agent@PROJECT.iam" \
  --limit=50 \
  --format="table(timestamp,protoPayload.methodName,protoPayload.status.message)"
```

## Self-Hosted Alternative: Cloud SQL Proxy + MCP

If the managed MCP is not yet available for your service, run a self-hosted MCP server that connects via Cloud SQL Auth Proxy:

```json
// Claude Code MCP config (local dev only)
{
  "mcpServers": {
    "cloudsql-local": {
      "command": "/path/to/cloudsql-mcp-server",
      "args": [
        "--instance=PROJECT:REGION:INSTANCE",
        "--database=mydb",
        "--read-only"
      ],
      "env": {
        "GOOGLE_APPLICATION_CREDENTIALS": ""
      }
    }
  }
}
```

Run the Cloud SQL Auth Proxy alongside:
```bash
./cloud-sql-proxy PROJECT:REGION:INSTANCE --port=5432 &
```

## Cloud SQL MCP Capabilities (Preview)

When enabled, the Cloud SQL MCP exposes these tools to AI agents:

- `list_databases` — list databases on the instance
- `describe_table` — schema inspection for a table
- `run_query` — execute a SQL query (read-only when SA has viewer role)
- `explain_query` — show query execution plan
- `list_tables` — list tables in a database

**Important:** The MCP inherits the SA's IAM permissions. A `cloudsql.viewer` SA can only read schema metadata, not execute DML.

## AlloyDB MCP Capabilities (Preview)

In addition to standard Cloud SQL capabilities:

- `vector_similarity_search` — semantic search using pgvector
- `explain_slow_query` — AI-powered slow query diagnosis
- `suggest_index` — automated index recommendation

## Production Constraints

- Do not connect MCP servers to production databases by default.
- Route MCP access to a read replica or a separate analytics instance.
- Use VPC Service Controls to prevent MCP access from outside the authorized perimeter.
- Review every tool call in AI agent audit logs — treat MCP database access like production SSH access.
