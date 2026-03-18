# Azure Key Vault Patterns

---

## Access Model: RBAC vs Access Policies

Use **RBAC** for all new Key Vaults. Access policies are a legacy model and will not receive new features.

```bash
# Create Key Vault with RBAC enabled
az keyvault create \
  --name <vault-name> \
  --resource-group <rg> \
  --location eastus \
  --enable-rbac-authorization true \
  --enable-soft-delete true \
  --retention-days 7 \
  --enable-purge-protection true   # Required for HSM-backed vaults and production

# Assign role to a managed identity
PRINCIPAL_ID=$(az identity show --name <identity> -g <rg> --query principalId -o tsv)
VAULT_ID=$(az keyvault show --name <vault-name> -g <rg> --query id -o tsv)

az role assignment create \
  --assignee-object-id "$PRINCIPAL_ID" \
  --assignee-principal-type ServicePrincipal \
  --role "Key Vault Secrets User" \
  --scope "$VAULT_ID"
```

### Key Vault RBAC Roles

| Role | Capabilities |
|------|-------------|
| `Key Vault Secrets User` | Get, list secret values (read-only) |
| `Key Vault Secrets Officer` | Get, set, delete, backup, restore secrets |
| `Key Vault Crypto User` | Sign, verify, encrypt, decrypt (not import keys) |
| `Key Vault Crypto Officer` | Create, import, update, delete keys; sign, verify |
| `Key Vault Certificate User` | Get certificate contents (read-only) |
| `Key Vault Certificate Officer` | Create, import, update, delete certificates |
| `Key Vault Administrator` | All operations on all object types |
| `Key Vault Reader` | Read metadata only — cannot read secret values |

---

## Reading Secrets in Application Code

```python
# Python
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

credential = DefaultAzureCredential()
client = SecretClient(vault_url="https://<vault-name>.vault.azure.net", credential=credential)

secret = client.get_secret("<secret-name>")
print(secret.value)
```

```go
// Go
import (
    "github.com/Azure/azure-sdk-for-go/sdk/azidentity"
    "github.com/Azure/azure-sdk-for-go/sdk/security/keyvault/azsecrets"
)

credential, _ := azidentity.NewDefaultAzureCredential(nil)
client, _ := azsecrets.NewClient("https://<vault-name>.vault.azure.net", credential, nil)

resp, err := client.GetSecret(ctx, "<secret-name>", "", nil)
if err != nil {
    return fmt.Errorf("getting secret: %w", err)
}
value := *resp.Value
```

```typescript
// TypeScript
import { DefaultAzureCredential } from "@azure/identity";
import { SecretClient } from "@azure/keyvault-secrets";

const credential = new DefaultAzureCredential();
const client = new SecretClient("https://<vault-name>.vault.azure.net", credential);

const secret = await client.getSecret("<secret-name>");
console.log(secret.value);
```

---

## Key Vault References (Recommended Pattern)

Key Vault references allow App Service, Container Apps, and Azure Functions to read secrets at runtime without any application code change — the platform resolves `@Microsoft.KeyVault(...)` references in app settings.

```bash
# Set an app setting that references a Key Vault secret
az webapp config appsettings set \
  --name <app> \
  --resource-group <rg> \
  --settings "MY_SECRET=@Microsoft.KeyVault(SecretUri=https://<vault-name>.vault.azure.net/secrets/<secret-name>/)"

# Grant the App Service's system-assigned identity access to Key Vault
IDENTITY=$(az webapp identity assign --name <app> -g <rg> --query principalId -o tsv)
az role assignment create \
  --assignee-object-id "$IDENTITY" \
  --assignee-principal-type ServicePrincipal \
  --role "Key Vault Secrets User" \
  --scope "$(az keyvault show --name <vault-name> -g <rg> --query id -o tsv)"
```

With this pattern, the app reads `MY_SECRET` from the environment — no Key Vault SDK needed. The reference is resolved by the Azure platform before the app starts.

---

## Certificate Management

```bash
# Create a self-signed certificate (dev/testing)
az keyvault certificate create \
  --vault-name <vault-name> \
  --name <cert-name> \
  --policy "$(az keyvault certificate get-default-policy)"

# Import an existing PFX certificate
az keyvault certificate import \
  --vault-name <vault-name> \
  --name <cert-name> \
  --file certificate.pfx \
  --password <pfx-password>

# List certificates
az keyvault certificate list --vault-name <vault-name> --output table

# Get certificate (returns CER — public key only)
az keyvault certificate show --vault-name <vault-name> --name <cert-name>
```

---

## Automatic Secret Rotation

Use Event Grid + Azure Functions to trigger rotation when a secret or certificate approaches expiry.

```bash
# Subscribe to Key Vault events
az eventgrid event-subscription create \
  --name <subscription-name> \
  --source-resource-id $(az keyvault show --name <vault-name> -g <rg> --query id -o tsv) \
  --endpoint <function-url> \
  --endpoint-type webhook \
  --included-event-types "Microsoft.KeyVault.SecretNearExpiry" \
                         "Microsoft.KeyVault.CertificateNearExpiry"
```

The function handler receives the event, generates a new secret value, stores it in Key Vault, and updates the dependent service (e.g., rotates a database password and updates the connection string).

---

## App Configuration Service Integration

Use App Configuration with Key Vault references for centralized config management:

```json
// App Configuration key-value where the value is a Key Vault reference
{
  "key": "Settings:ConnectionString",
  "value": "{\"uri\":\"https://<vault>.vault.azure.net/secrets/<secret>\"}",
  "contentType": "application/vnd.microsoft.appconfig.keyvaultref+json;charset=utf-8"
}
```

SDK resolves the reference transparently when `UseAzureAppConfiguration` / `AzureAppConfigurationProvider` is configured with a `KeyVaultOptions` credential.

---

## Anti-Patterns

- **Storing secrets in environment variables in code** (`.env` files, `appsettings.json`) — use Key Vault references or SDK clients with Managed Identity.
- **Using access policies instead of RBAC** for new vaults — access policies cannot be audited with standard Azure RBAC tooling.
- **Disabling soft delete** — if a secret is accidentally deleted, it is unrecoverable without soft delete enabled.
- **Overly broad role assignments** (`Key Vault Administrator`) — assign the narrowest role; use `Key Vault Secrets User` for read-only.
- **Not enabling purge protection** on production vaults — purge protection prevents permanent deletion during the soft-delete retention window, protecting against accidental or malicious purges.
- **Disabling MCP elicitation for Key Vault** (`--disable-user-confirmation`) — this allows an AI agent to read and return secrets without human review.
- **Caching secrets indefinitely** in application memory — respect the `expires_on` field; refresh before expiry to pick up rotated values without redeployment.
