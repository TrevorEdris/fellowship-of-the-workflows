# GCP MCP Server Configuration

## Official Google-Managed Remote MCPs (Recommended)

Google operates fully managed MCP servers with IAM-level access controls. No service account key files — OAuth/OIDC-based. These are the safest option for enterprise AI agent workflows.

| MCP Server | Status | Capabilities |
|------------|--------|-------------|
| **BigQuery** | GA (Dec 2025) | Schema introspection, query execution, in-place data access |
| **Compute Engine** | GA (Dec 2025) | VM provisioning, resizing, lifecycle management |
| **GKE** | GA (Dec 2025) | Cluster management, workload interaction, kubectl-equivalent operations |
| **Google Maps** | GA (Dec 2025) | Maps and geo operations |
| **AlloyDB** | Preview | Schema creation, complex query diagnosis, vector similarity search |
| **Cloud SQL** | Preview | Natural language DB interaction, query optimization (MySQL/PostgreSQL/SQLServer) |
| **Spanner** | Preview | Spanner Graph queries, relational + semantic data |
| **Bigtable** | Preview | — |
| **Firestore** | Preview | — |
| **Memorystore** | Planned | — |
| **Pub/Sub** | Planned | — |

**Enable from Cloud Console:** AI → MCP Servers → Enable for [service].

**Auth model:** IAM-controlled. Organization/folder/project policy enforcement. Fine-grained IAM per user/tool. Compliant with MCP authorization spec.

## gcloud-mcp (Official CLI-Wrapping MCP, Self-Hosted)

Provided by Google at [`googleapis/gcloud-mcp`](https://github.com/googleapis/gcloud-mcp). Wraps the gcloud CLI and exposes a `run_gcloud_command` tool plus structured logging tools.

### Configuration

```json
{
  "mcpServers": {
    "gcloud": {
      "command": "gcloud",
      "args": ["alpha", "mcp-server", "run"],
      "env": {
        "CLOUDSDK_CORE_PROJECT": "your-project-id"
      }
    }
  }
}
```

### Least-Privilege Setup

**Do not run gcloud-mcp as your personal admin gcloud account.** Instead, impersonate a scoped service account:

```bash
# Create a dedicated MCP service account with read-mostly permissions
gcloud iam service-accounts create mcp-agent-sa \
  --display-name="MCP Agent SA" \
  --description="Used by AI agent MCP tools — read-mostly"

# Grant read-only roles appropriate to the use case
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member=serviceAccount:mcp-agent-sa@PROJECT.iam.gserviceaccount.com \
  --role=roles/viewer

gcloud projects add-iam-policy-binding PROJECT_ID \
  --member=serviceAccount:mcp-agent-sa@PROJECT.iam.gserviceaccount.com \
  --role=roles/logging.viewer

# Configure ADC to impersonate this SA
gcloud auth application-default login \
  --impersonate-service-account=mcp-agent-sa@PROJECT.iam.gserviceaccount.com
```

### Restricted Command List

gcloud-mcp restricts which gcloud subcommands are available (safety measure). Audit the allowed list before enabling in production AI agent workflows:

```bash
# Review what commands are exposed
gcloud alpha mcp-server list-commands
```

## Community MCP Servers (Local Dev / Tooling Only)

These are not Google-maintained. Audit before using in production AI agent workflows.

### krzko/google-cloud-mcp

- **Repo:** [`krzko/google-cloud-mcp`](https://github.com/krzko/google-cloud-mcp)
- **Services:** Billing, IAM, Logging, Monitoring, Spanner, Error Reporting
- **Auth:** Service account key file or `GOOGLE_CLIENT_EMAIL` + `GOOGLE_PRIVATE_KEY` env vars

### eniayomi/gcp-mcp

- **Repo:** [`eniayomi/gcp-mcp`](https://github.com/eniayomi/gcp-mcp)
- **Services:** Compute, GCS, Cloud Functions, Cloud Run, BigQuery, GKE, Cloud SQL, Logging, Billing
- **Notable:** `run-gcp-code` TypeScript execution capability
- **Auth:** `GOOGLE_APPLICATION_CREDENTIALS` (JSON key path)
- **Warning:** The `run-gcp-code` arbitrary execution capability requires careful sandboxing and command allowlisting.

## Security Hardening for GCP MCPs

| Risk | Mitigation |
|------|-----------|
| Service account key files in MCP config | Use ADC (metadata server or WIF) or gcloud impersonation; avoid key files |
| Over-privileged MCP service account | Create a dedicated, read-mostly MCP SA; avoid `roles/editor` or `roles/owner` |
| `run_gcloud_command` arbitrary execution | Audit gcloud-mcp's allowed command list; restrict to read-only subcommands |
| `run-gcp-code` execution (eniayomi) | Whitelist specific operations; do not connect to production projects |
| Community server trust | Not Google-maintained — review source code before production use |
| Credential exposure via process env | Never pass `GOOGLE_APPLICATION_CREDENTIALS` as a raw JSON string; mount as file or use ADC |
| MCP server over-reach | Bind each MCP server to the minimum project scope needed |

## Configuration Examples for Claude Code

### Official managed servers (recommended)

No local config required — authentication is handled via your browser OAuth session in the Claude interface.

### gcloud-mcp in Claude Code

Add to `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS):

```json
{
  "mcpServers": {
    "gcloud-read-only": {
      "command": "gcloud",
      "args": ["alpha", "mcp-server", "run", "--project=YOUR_PROJECT_ID"],
      "env": {}
    }
  }
}
```

**Important:** Ensure `gcloud auth application-default login --impersonate-service-account=mcp-agent-sa@PROJECT.iam.gserviceaccount.com` is run before starting Claude.
