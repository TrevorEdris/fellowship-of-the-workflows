# Azure Blob Storage Patterns

---

## Authentication: Managed Identity vs SAS Tokens

| Approach | When to Use | How |
|----------|-------------|-----|
| **Managed Identity** (preferred) | Application code in Azure compute | Assign `Storage Blob Data Contributor` (or Reader) to the managed identity; use `DefaultAzureCredential` in SDK |
| **SAS Token** | Time-scoped external delegation, CDN, signed URLs for clients | Generate via SDK or CLI; set shortest practical expiry |
| **Storage Account Key** | Terraform state backend, legacy scripts | Never in application code; rotate regularly; use Key Vault for storage |
| **Connection String** | Local development only (`UseDevelopmentStorage=true` / Azurite) | Never in production; use Managed Identity |

---

## SDK Patterns

### Go

```go
import (
    "github.com/Azure/azure-sdk-for-go/sdk/azidentity"
    "github.com/Azure/azure-sdk-for-go/sdk/storage/azblob"
)

credential, err := azidentity.NewDefaultAzureCredential(nil)
if err != nil {
    return fmt.Errorf("creating credential: %w", err)
}

client, err := azblob.NewClient(
    "https://<account>.blob.core.windows.net",
    credential,
    nil,
)
```

### Python

```python
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient

credential = DefaultAzureCredential()
client = BlobServiceClient(
    account_url="https://<account>.blob.core.windows.net",
    credential=credential,
)

# Upload
with open("file.txt", "rb") as f:
    blob_client = client.get_blob_client(container="mycontainer", blob="file.txt")
    blob_client.upload_blob(f, overwrite=True)
```

### TypeScript

```typescript
import { DefaultAzureCredential } from "@azure/identity";
import { BlobServiceClient } from "@azure/storage-blob";

const credential = new DefaultAzureCredential();
const client = new BlobServiceClient(
  "https://<account>.blob.core.windows.net",
  credential
);

const containerClient = client.getContainerClient("mycontainer");
await containerClient.uploadBlockBlob("file.txt", data, data.length);
```

---

## SAS Token Generation

```bash
# CLI: generate a blob SAS token (1-hour read access)
az storage blob generate-sas \
  --account-name <account> \
  --container-name <container> \
  --name <blob-path> \
  --permissions r \
  --expiry $(date -u -d "1 hour" '+%Y-%m-%dT%H:%MZ') \
  --auth-mode login \  # Use your az login credential, not account key
  --output tsv

# SDK (Python): user delegation SAS (uses Managed Identity — preferred over account key SAS)
from azure.storage.blob import generate_blob_sas, BlobSasPermissions
from datetime import datetime, timezone, timedelta

sas_token = generate_blob_sas(
    account_name="<account>",
    container_name="<container>",
    blob_name="<blob>",
    account_key=None,
    user_delegation_key=service_client.get_user_delegation_key(
        key_start_time=datetime.now(timezone.utc),
        key_expiry_time=datetime.now(timezone.utc) + timedelta(hours=1),
    ),
    permission=BlobSasPermissions(read=True),
    expiry=datetime.now(timezone.utc) + timedelta(hours=1),
)
```

---

## Lifecycle Management

Define lifecycle policies to automatically tier or delete blobs based on age, reducing storage costs.

```bash
# Apply a lifecycle policy via JSON definition
az storage account management-policy create \
  --account-name <account> \
  --resource-group <rg> \
  --policy @lifecycle-policy.json
```

**`lifecycle-policy.json` example:**

```json
{
  "rules": [
    {
      "name": "archiveOldBlobs",
      "enabled": true,
      "type": "Lifecycle",
      "definition": {
        "filters": {
          "blobTypes": ["blockBlob"],
          "prefixMatch": ["logs/", "backups/"]
        },
        "actions": {
          "baseBlob": {
            "tierToCool": { "daysAfterModificationGreaterThan": 30 },
            "tierToArchive": { "daysAfterModificationGreaterThan": 90 },
            "delete": { "daysAfterModificationGreaterThan": 365 }
          },
          "snapshot": {
            "delete": { "daysAfterCreationGreaterThan": 30 }
          }
        }
      }
    }
  ]
}
```

---

## Private Endpoints

Disable public internet access and route storage traffic through VNet.

```bash
# Disable public access
az storage account update \
  --name <account> \
  --resource-group <rg> \
  --public-network-access Disabled

# Create private endpoint (requires VNet and subnet)
az network private-endpoint create \
  --name <account>-pe \
  --resource-group <rg> \
  --vnet-name <vnet> \
  --subnet <subnet> \
  --private-connection-resource-id $(az storage account show --name <account> -g <rg> --query id -o tsv) \
  --group-id blob \
  --connection-name <account>-pe-conn
```

Pair with a **Private DNS Zone** (`privatelink.blob.core.windows.net`) linked to the VNet so DNS resolves to the private endpoint IP.

---

## Anti-Patterns

- **Connection strings in app config or environment variables** — use Managed Identity and SDK clients.
- **Account key SAS tokens** (signed with storage key) instead of **user delegation SAS** (signed with Entra ID) — user delegation SAS is revocable via the managed identity.
- **`Allow all networks` (public access enabled) for production storage** — use Private Endpoints or at minimum IP-restrict to known CIDRs.
- **Soft delete disabled** — enable soft delete for blobs and containers to recover accidental deletions.
- **No lifecycle policy** — unmanaged blobs accumulate indefinitely; define lifecycle rules at storage account creation.
