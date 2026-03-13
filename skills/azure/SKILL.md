---
name: azure
description: "Azure platform guidance covering authentication (Managed Identity, Entra ID, RBAC), Azure CLI patterns, IaC decision tree (Bicep vs Terraform), Azure MCP Server setup, and common service patterns (Storage, Cosmos DB, Key Vault, AKS). Use when building, deploying, or debugging Azure workloads."
user-invocable: true
argument-hint: "[auth|cli|iac|mcp|storage|cosmos|keyvault|aks]"
model: sonnet
---

# Azure

Comprehensive guidance for Azure workloads: authentication, CLI tooling, infrastructure-as-code, MCP integration, and core service patterns.

---

## When to Use

- Setting up authentication for an Azure workload (Managed Identity, Entra ID, Service Principal)
- Writing or reviewing Azure CLI commands and scripts
- Choosing between Bicep and Terraform for Azure IaC
- Configuring the Azure MCP Server for an AI agent workflow
- Implementing patterns for Blob Storage, Cosmos DB, Key Vault, or AKS
- Auditing Azure security posture (connection strings, RBAC scope, Key Vault access)

---

## Quick Start

```
/azure auth      # Authentication: Managed Identity, Entra ID, RBAC, DefaultAzureCredential
/azure cli       # Azure CLI: subscription switching, MFA, OIDC for pipelines, azd
/azure iac       # IaC: Bicep vs Terraform decision tree and patterns
/azure mcp       # Azure MCP Server: install, namespace config, security flags
/azure storage   # Blob Storage: SAS tokens vs managed identity, lifecycle, SDK patterns
/azure cosmos    # Cosmos DB: partition keys, consistency, SDK usage
/azure keyvault  # Key Vault: secrets, certificates, App Config references
/azure aks       # AKS: Workload Identity, KEDA, ACR integration, aks-mcp
```

No argument? Ask what service or topic is needed.

---

## Authentication Reference

### DefaultAzureCredential Chain (all languages)

```
1. Environment variables (AZURE_CLIENT_ID, AZURE_CLIENT_SECRET / AZURE_FEDERATED_TOKEN_FILE)
2. Workload Identity (Kubernetes — via AZURE_FEDERATED_TOKEN_FILE)
3. Managed Identity (IMDS endpoint — available in Azure compute)
4. Azure CLI (az login — local dev)
5. Azure PowerShell / Visual Studio / VS Code (local dev fallbacks)
```

**Production rule:** Pin the credential type explicitly — do not rely on the full chain in production. Use `ManagedIdentityCredential` or `WorkloadIdentityCredential` directly to prevent unexpected fallbacks.

**Local dev:** `DefaultAzureCredential` is correct — it falls through to `az login` automatically.

### Credential Selection Guide

| Environment | Credential | Notes |
|-------------|-----------|-------|
| Azure VMs / App Service / Container Apps | `ManagedIdentityCredential` | System-assigned preferred; no secrets to rotate |
| AKS pods | `WorkloadIdentityCredential` | Replaces pod identity; requires federated credential on the managed identity |
| GitHub Actions CI | OIDC federated credential | No long-lived secret; `azure/login` action; see `references/azure-cli-patterns.md` |
| Azure DevOps CI | OIDC service connection | ADO service connection with Workload Identity Federation (no secret) |
| Local dev | `AzureCliCredential` or full `DefaultAzureCredential` | `az login` handles auth |

### RBAC Principles

- Assign roles at the **resource group or resource level**, not subscription level, unless cross-resource access is genuinely needed.
- Prefer built-in roles (`Storage Blob Data Reader`, `Key Vault Secrets User`) over custom roles.
- Audit assignments: `az role assignment list --assignee <principal-id> --output table`
- Use `--condition` for attribute-based access control (ABAC) on Storage when fine-grained blob access is needed.

### SDK Authentication Per Language

| Language | Package | Pattern |
|----------|---------|---------|
| Go | `github.com/Azure/azure-sdk-for-go/sdk/azidentity` | `azidentity.NewDefaultAzureCredential(nil)` |
| Python | `azure-identity` | `DefaultAzureCredential()` / `azure.identity.aio.DefaultAzureCredential()` for async |
| TypeScript | `@azure/identity` | `new DefaultAzureCredential()` |
| .NET / C# | `Azure.Identity` | `new DefaultAzureCredential()` / DI: `services.AddAzureClients(b => b.UseCredential(...))` |

See language-specific references in the respective `*-patterns` skill:
- Go: `go-patterns/references/azure-go.md`
- Python: `python-patterns/references/azure-python.md`
- TypeScript: `typescript-patterns/references/azure-typescript.md`

---

## IaC Decision Tree

```
Working exclusively with Azure?
  YES → Small/new team or Azure-native shop?
    YES → Bicep (no state management, native Azure preview support, simpler syntax)
    NO  → Already using Terraform elsewhere?
      YES → Terraform (azurerm provider — consistent with existing tooling)
      NO  → Bicep (recommended for Azure-only organizations)
  NO (multi-cloud or SaaS providers in scope) → Terraform
  Have existing ARM templates? → Decompile: az bicep decompile --file template.json
```

| IaC Tool | State | Best For | Key Commands |
|----------|-------|----------|-------------|
| Bicep | None (server-side) | Azure-only; simple; no state mgmt overhead | `az deployment group create`, `az bicep build` |
| Terraform | Required (use Azure Storage backend) | Multi-cloud; existing Terraform estate | `terraform init/plan/apply` |
| ARM JSON | None | Legacy only — prefer Bicep for new authoring | N/A — decompile to Bicep |

See `references/iac-decision-guide.md` for detailed examples and patterns.

---

## Azure CLI Quick Reference

```bash
# Subscription management
az account list --output table
az account set --subscription "<name-or-id>"
az account show --query name -o tsv

# Login
az login                          # Interactive (opens browser)
az login --use-device-code        # Headless / SSH sessions
az login --service-principal -u <app-id> -p <password> --tenant <tenant>

# Set defaults (avoids repeating --resource-group and --location)
az config set defaults.group=<rg> defaults.location=eastus

# Common resource commands
az group list --output table
az resource list --resource-group <rg> --output table
az resource show --ids <resource-id>
```

**MFA Note (as of Oct 2025):** MFA is mandatory for all write operations via Azure CLI. Use OIDC federated credentials in pipelines to avoid interactive MFA requirements.

See `references/azure-cli-patterns.md` for OIDC pipeline setup, azd, and Bicep CLI patterns.

---

## Azure MCP Server

The official Microsoft Azure MCP Server (`azmcp`) exposes 47+ Azure services as MCP tools.

```bash
# Install
npm install -g @azure/mcp-server   # or via winget / brew

# Run (scope to only the services your agent needs)
npx @azure/mcp-server --namespace storage,keyvault
npx @azure/mcp-server --read-only           # Query-only; no mutations
```

**Security requirements:**
- Use Managed Identity or `az login` credential — never storage account keys or connection strings.
- Enable elicitation (default) — do not use `--disable-user-confirmation` in production. The server prompts before returning Key Vault secrets.
- Scope namespaces to principle of least privilege: `--namespace storage,keyvault`.
- Use `--read-only` for exploration and developer audit workflows.

See `references/azure-mcp-setup.md` for full configuration, namespace list, and MCP client config examples.

---

## Common Service Patterns

### Blob Storage

- **Auth:** Managed Identity + `Storage Blob Data Contributor` role. SAS tokens only for time-scoped external delegation.
- **SDK:** Use the Azure SDK client (`BlobServiceClient`, `BlobContainerClient`) — do not use connection strings in code.
- **Lifecycle:** Define lifecycle management policies for cost control (tier to Cool after 30 days, delete after 365).
- **Private access:** Use Private Endpoints + VNet integration; disable public blob access at storage account level.

See `references/storage-patterns.md`.

### Cosmos DB

- **Partition key:** The single most important design decision. Choose a key with high cardinality and uniform distribution. Avoid hot partitions.
- **Consistency:** Default `Session` consistency. Use `Eventual` for read-heavy non-critical data; `Strong` only when cross-region linearizability is required (latency penalty).
- **Auth:** Managed Identity + `Cosmos DB Built-in Data Contributor` role. Avoid primary/secondary keys in application code.

See `references/cosmos-db-patterns.md`.

### Key Vault

- **Access model:** Use RBAC (not access policies) for new vaults — `Key Vault Secrets User` for read, `Key Vault Secrets Officer` for write.
- **References:** Use Key Vault references in App Service / Container Apps app settings — avoids reading secrets in application startup code.
- **MCP:** The Azure MCP Server requires user confirmation (elicitation) before returning secrets. Do not disable this.
- **Rotation:** Use Event Grid + Functions to trigger automatic rotation on certificate/secret expiry.

See `references/key-vault-patterns.md`.

### AKS

- **Workload Identity:** Use Azure Workload Identity (federated credentials on managed identity) — pod identity (AAD Pod Identity) is deprecated.
- **ACR integration:** Attach ACR to AKS cluster: `az aks update --attach-acr <registry-name>`. This grants `AcrPull` to the kubelet managed identity.
- **Scaling:** KEDA with Azure Service Bus or Event Hubs scalers for event-driven workloads.
- **MCP:** `aks-mcp` (MIT, GA Aug 2025) provides K8s operations on AKS for AI agents.

See `references/aks-patterns.md`.

---

## Key References

| Reference | Contents |
|-----------|----------|
| `references/authentication.md` | DefaultAzureCredential chain, Managed Identity setup, RBAC patterns |
| `references/azure-cli-patterns.md` | az commands, subscription switching, OIDC, azd, Bicep CLI |
| `references/iac-decision-guide.md` | Bicep vs Terraform decision tree with examples |
| `references/azure-mcp-setup.md` | azmcp install, namespace config, security flags, MCP client JSON |
| `references/storage-patterns.md` | Blob Storage SDK patterns, SAS, lifecycle, private endpoints |
| `references/cosmos-db-patterns.md` | Partition key design, SDK usage, consistency levels |
| `references/key-vault-patterns.md` | Secrets, certificates, Key Vault references, rotation |
| `references/aks-patterns.md` | Workload Identity, KEDA, ACR, aks-mcp |
