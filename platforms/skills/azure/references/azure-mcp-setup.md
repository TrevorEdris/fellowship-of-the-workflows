# Azure MCP Server Setup

The official Microsoft Azure MCP Server (`azmcp`) exposes 47+ Azure services as MCP tools for AI agents.

**Source:** Moved from `Azure/azure-mcp` (archived Aug 2025) to `microsoft/mcp` catalog.
**Status:** GA v1.0 (October 2025).

---

## Installation

```bash
# npm (cross-platform)
npm install -g @azure/mcp-server

# Verify installation
npx @azure/mcp-server --version
```

### macOS via Homebrew (if available in tap)

```bash
brew install azure/tap/azure-mcp
```

---

## Authentication

The server authenticates using the same `DefaultAzureCredential` chain as the Azure SDK:

1. Azure CLI (`az login`) — recommended for local development
2. Managed Identity — for agents running on Azure compute
3. Environment variables (`AZURE_CLIENT_ID`, `AZURE_TENANT_ID`, `AZURE_CLIENT_SECRET` / `AZURE_FEDERATED_TOKEN_FILE`)

**Never configure with storage account keys or connection strings** — RBAC is the correct auth model.

---

## Starting the Server

```bash
# Basic — all namespaces, read-write
npx @azure/mcp-server

# Scope to specific namespaces (principle of least privilege)
npx @azure/mcp-server --namespace storage,keyvault

# Read-only mode — no mutations (recommended for exploration)
npx @azure/mcp-server --read-only

# Combine namespace scoping with read-only
npx @azure/mcp-server --namespace storage,keyvault --read-only

# Specify subscription (overrides az account default)
npx @azure/mcp-server --subscription <subscription-id>
```

---

## Security Flags

| Flag | Behavior | Recommendation |
|------|----------|---------------|
| `--read-only` | Disables all write/delete operations | Use for exploration and audit workflows |
| `--namespace <list>` | Restricts to listed service namespaces | Always scope to only what the agent needs |
| `--disable-user-confirmation` | Bypasses elicitation prompts for Key Vault secrets | Never disable in production or untrusted environments |
| `--subscription <id>` | Restricts to a single subscription | Recommended to prevent cross-subscription operations |

**Elicitation (user confirmation):** The server prompts the user before returning Key Vault secrets, connection strings, or certificate private keys. This is a security control — disabling it allows an AI agent to exfiltrate secrets without human review.

---

## Available Namespaces

| Namespace | Services Covered |
|-----------|-----------------|
| `storage` | Blob containers, blobs, queues, tables, file shares |
| `keyvault` | Secrets, keys, certificates |
| `cosmosdb` | Databases, containers, documents, queries |
| `aks` | Clusters, node pools, credentials (not a replacement for aks-mcp) |
| `sql` | Azure SQL servers, databases, query execution |
| `postgresql` | Azure Database for PostgreSQL |
| `mysql` | Azure Database for MySQL |
| `redis` | Azure Cache for Redis |
| `servicebus` | Namespaces, queues, topics, subscriptions |
| `eventhubs` | Namespaces, event hubs, consumer groups |
| `eventgrid` | Topics, event subscriptions |
| `monitor` | Log Analytics workspaces, KQL queries |
| `appconfig` | Configuration stores, key-values, feature flags |
| `appservice` | Web apps, deployment slots, app settings |
| `containerregistry` | Registries, repositories, images |
| `bicep` | Schema validation and intellisense for Bicep |
| `deploy` | Deployment operations and what-if |
| `rbac` | Role definitions, role assignments |
| `pricing` | Azure pricing calculator API |
| `advisor` | Azure Advisor recommendations |
| `policy` | Policy definitions and assignments |
| `aifoundry` | Azure AI Foundry (model deployments, prompts) |
| `aisearch` | Azure AI Search indexes and documents |
| `grafana` | Azure Managed Grafana dashboards |

---

## MCP Client Configuration

### Claude Code (`.claude/settings.json`)

```json
{
  "mcpServers": {
    "azure": {
      "command": "npx",
      "args": [
        "@azure/mcp-server",
        "--namespace", "storage,keyvault,cosmosdb",
        "--read-only"
      ]
    }
  }
}
```

### Cursor (`.cursor/mcp.json`)

```json
{
  "mcpServers": {
    "azure": {
      "command": "npx",
      "args": ["@azure/mcp-server", "--namespace", "storage,keyvault"]
    }
  }
}
```

### Claude Desktop (`claude_desktop_config.json`)

```json
{
  "mcpServers": {
    "azure": {
      "command": "npx",
      "args": [
        "@azure/mcp-server",
        "--namespace", "storage,keyvault",
        "--subscription", "<subscription-id>"
      ]
    }
  }
}
```

---

## Azure DevOps MCP Server

Separate from the Azure MCP Server — covers ADO work items, PRs, repos, wikis, builds, and releases.

**Source:** `microsoft/azure-devops-mcp`
**Auth:** PAT or OAuth
**Important:** Designed to run locally or in-network. Do not expose as a remote server — it accesses private DevOps data.

```json
{
  "mcpServers": {
    "azure-devops": {
      "command": "npx",
      "args": ["@microsoft/azure-devops-mcp"],
      "env": {
        "AZURE_DEVOPS_ORG": "https://dev.azure.com/<org>",
        "AZURE_DEVOPS_PAT": "<pat-token>"
      }
    }
  }
}
```

---

## AKS MCP Server (Community)

For Kubernetes operations on AKS — separate from the Azure MCP Server.

**Source:** AKS Engineering Blog announcement (Aug 2025), MIT license.
**Compatible with:** Claude, Cursor, Copilot.

```bash
# Install
npm install -g @azure/aks-mcp

# Run
npx @azure/aks-mcp
```

The AKS MCP Server provides cluster, node pool, and workload operations that the main Azure MCP Server's `aks` namespace does not fully cover.

---

## Verification

After configuring, verify the server is accessible from your MCP client:

```
# In Claude / Cursor: ask the AI to list your Azure resource groups
"List my Azure resource groups"
# Expected: The AI uses the azure MCP tool to call az account list
```

If the server is not found, check:
1. `npx @azure/mcp-server --version` resolves without error
2. The MCP client config path is correct for your tool
3. `az account show` succeeds (you are authenticated)
