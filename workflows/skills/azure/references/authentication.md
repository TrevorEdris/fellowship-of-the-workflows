# Azure Authentication Reference

Covers Entra ID, Managed Identity, RBAC, and the DefaultAzureCredential chain across all supported languages.

---

## DefaultAzureCredential Probe Order

The credential chain is probed in this order at runtime. The first credential that succeeds is used.

| # | Credential | Triggered By |
|---|-----------|-------------|
| 1 | `EnvironmentCredential` | `AZURE_CLIENT_ID` + `AZURE_CLIENT_SECRET` or `AZURE_FEDERATED_TOKEN_FILE` set |
| 2 | `WorkloadIdentityCredential` | `AZURE_FEDERATED_TOKEN_FILE` present (Kubernetes Workload Identity) |
| 3 | `ManagedIdentityCredential` | IMDS endpoint available (Azure compute: VMs, App Service, Container Apps, Functions) |
| 4 | `SharedTokenCacheCredential` | Windows only; Visual Studio token cache |
| 5 | `VisualStudioCodeCredential` | VS Code Azure Account extension sign-in |
| 6 | `AzureCliCredential` | `az login` session |
| 7 | `AzurePowerShellCredential` | `Connect-AzAccount` session |
| 8 | `AzureDeveloperCliCredential` | `azd auth login` session |

**Production guidance:** Do not rely on the full chain in production. Pin the credential:

```python
# Python — production pinning
from azure.identity import ManagedIdentityCredential
credential = ManagedIdentityCredential()  # system-assigned
# or: ManagedIdentityCredential(client_id="<user-assigned-client-id>")
```

```go
// Go — production pinning
import "github.com/Azure/azure-sdk-for-go/sdk/azidentity"
credential, err := azidentity.NewManagedIdentityCredential(nil)
// or user-assigned: azidentity.NewManagedIdentityCredential(&azidentity.ManagedIdentityCredentialOptions{
//     ID: azidentity.ClientID("<client-id>"),
// })
```

```typescript
// TypeScript — production pinning
import { ManagedIdentityCredential } from "@azure/identity";
const credential = new ManagedIdentityCredential(); // system-assigned
// or: new ManagedIdentityCredential("<client-id>") // user-assigned
```

---

## Managed Identity Setup

### System-Assigned (simpler, 1:1 with resource)

```bash
# Enable on existing App Service
az webapp identity assign --name <app> --resource-group <rg>

# Enable on existing VM
az vm identity assign --name <vm> --resource-group <rg>

# Enable on existing AKS node pool kubelet
# Automatically created with cluster — use az aks show to get the identity
az aks show --name <cluster> --resource-group <rg> --query identityProfile
```

### User-Assigned (portable, reusable across resources)

```bash
# Create the identity
az identity create --name <identity-name> --resource-group <rg>

# Get client ID and principal ID
CLIENT_ID=$(az identity show --name <identity-name> -g <rg> --query clientId -o tsv)
PRINCIPAL_ID=$(az identity show --name <identity-name> -g <rg> --query principalId -o tsv)

# Assign to App Service
az webapp identity assign \
  --name <app> \
  --resource-group <rg> \
  --identities /subscriptions/<sub>/resourceGroups/<rg>/providers/Microsoft.ManagedIdentity/userAssignedIdentities/<identity-name>
```

### Workload Identity (AKS)

Workload Identity uses OIDC federation — the Kubernetes service account token is exchanged for an Azure access token without long-lived secrets.

```bash
# 1. Enable OIDC issuer and Workload Identity on the cluster
az aks update --name <cluster> --resource-group <rg> \
  --enable-oidc-issuer \
  --enable-workload-identity

# 2. Get the OIDC issuer URL
OIDC_ISSUER=$(az aks show --name <cluster> -g <rg> --query "oidcIssuerProfile.issuerUrl" -o tsv)

# 3. Create user-assigned managed identity (if not already done)
az identity create --name <workload-identity> --resource-group <rg>

# 4. Create federated credential linking the K8s service account to the managed identity
az identity federated-credential create \
  --name <federated-cred-name> \
  --identity-name <workload-identity> \
  --resource-group <rg> \
  --issuer "$OIDC_ISSUER" \
  --subject "system:serviceaccount:<k8s-namespace>:<k8s-service-account>" \
  --audience api://AzureADTokenExchange

# 5. Annotate the K8s service account
kubectl annotate serviceaccount <sa> \
  --namespace <namespace> \
  azure.workload.identity/client-id=<client-id>
```

---

## RBAC Role Assignments

### Common Built-In Roles

| Role | Use Case |
|------|----------|
| `Storage Blob Data Reader` | Read blob data |
| `Storage Blob Data Contributor` | Read + write blob data |
| `Key Vault Secrets User` | Read secrets |
| `Key Vault Secrets Officer` | Create, update, delete secrets |
| `Key Vault Crypto User` | Sign, verify, encrypt, decrypt (keys) |
| `Cosmos DB Built-in Data Reader` | Read Cosmos DB documents |
| `Cosmos DB Built-in Data Contributor` | Read + write Cosmos DB documents |
| `AcrPull` | Pull images from Azure Container Registry |
| `AcrPush` | Push images to Azure Container Registry |

### Assigning a Role

```bash
# Get the managed identity principal ID
PRINCIPAL_ID=$(az identity show --name <identity> -g <rg> --query principalId -o tsv)

# Assign Storage Blob Data Contributor at resource group scope
az role assignment create \
  --assignee-object-id "$PRINCIPAL_ID" \
  --assignee-principal-type ServicePrincipal \
  --role "Storage Blob Data Contributor" \
  --scope /subscriptions/<sub>/resourceGroups/<rg>

# Assign at individual resource scope (more restrictive — preferred)
az role assignment create \
  --assignee-object-id "$PRINCIPAL_ID" \
  --assignee-principal-type ServicePrincipal \
  --role "Storage Blob Data Reader" \
  --scope /subscriptions/<sub>/resourceGroups/<rg>/providers/Microsoft.Storage/storageAccounts/<account>
```

### Audit Assignments

```bash
# List all role assignments for a principal
az role assignment list --assignee <principal-id-or-email> --output table

# List all role assignments on a resource
az role assignment list --scope <resource-id> --output table

# Check effective permissions (what can a principal do on a resource?)
az role assignment list --assignee <principal-id> --scope <resource-id> --all
```

---

## Service Principal vs Managed Identity

| Criteria | Managed Identity | Service Principal |
|----------|-----------------|-------------------|
| Secret rotation | None required | Required (client secret expires) |
| Supported environments | Azure compute only | Anywhere with network access |
| CI/CD pipelines | Via OIDC federated credential | Long-lived secret or OIDC |
| Local dev | Falls back to `az login` | Requires env vars or secret store |
| Recommended for Azure workloads | Yes | Only when Managed Identity unavailable |

---

## Anti-Patterns

- **Hardcoded connection strings or storage keys** in application code or `appsettings.json` — use Managed Identity and SDK clients instead.
- **Subscription-scope RBAC assignments** — always scope as narrowly as possible (resource or resource group).
- **Disabling access policies in favor of RBAC on existing Key Vaults** without migrating all existing policy assignments first — this will break access immediately.
- **Using `DefaultAzureCredential` in production without pinning** — unexpected fallback to `AzureCliCredential` in production if IMDS is unreachable will fail with a confusing error.
- **Registering multiple `DefaultAzureCredential` instances in .NET DI** — each has its own token cache; use `services.AddAzureClients` with `UseCredential(new DefaultAzureCredential())` to share the cache.
