# Azure Cosmos DB Patterns

---

## Partition Key Design

The partition key is the single most important decision in a Cosmos DB data model. A bad partition key causes hot partitions, request throttling, and cross-partition queries.

### Good Partition Key Properties

| Property | Explanation |
|----------|-------------|
| **High cardinality** | Many distinct values — avoids concentrating all data in one partition |
| **Uniform distribution** | Traffic and storage distributed evenly across partitions |
| **Aligned with query access patterns** | Most queries include the partition key in the filter |
| **Immutable** | Partition key values cannot be updated after document creation |

### Common Patterns

| Scenario | Good Partition Key | Anti-Pattern |
|----------|--------------------|-------------|
| Multi-tenant SaaS | `tenantId` | `userId` if one tenant has many users |
| E-commerce orders | `customerId` | `orderId` (too many partitions with tiny data each) |
| IoT telemetry | `deviceId` + date bucket | `timestamp` (sequential — hot partition at write head) |
| Social posts | `userId` | `type` (low cardinality) |
| Audit logs | `entityId` | `eventType` (low cardinality) |

### Synthetic Partition Keys

When no single field provides good distribution, combine fields:

```json
{
  "id": "12345",
  "partitionKey": "tenant-A:user-456",
  "tenantId": "tenant-A",
  "userId": "user-456"
}
```

---

## Consistency Levels

Ordered from strongest to weakest. Stronger consistency = higher latency and lower availability.

| Level | Description | Use When |
|-------|-------------|----------|
| **Strong** | Linearizable — reads always see the latest write globally | Financial transactions requiring cross-region linearizability |
| **Bounded Staleness** | Reads lag writes by at most K versions or T seconds | Globally distributed apps needing near-strong consistency |
| **Session** (default) | Consistent within a single client session | Most applications — read your own writes guaranteed |
| **Consistent Prefix** | Reads never see out-of-order writes | Apps that can tolerate stale data but need ordering |
| **Eventual** | Lowest latency, no ordering guarantees | Read-heavy, non-critical data (counts, recommendations) |

**Recommendation:** Start with `Session` consistency (the default). Change only when you have a measured latency or cost problem.

---

## Authentication

Use Managed Identity + RBAC, not primary/secondary keys.

```bash
# Assign Cosmos DB Built-in Data Contributor role
PRINCIPAL_ID=$(az identity show --name <identity> -g <rg> --query principalId -o tsv)
COSMOS_RESOURCE_ID=$(az cosmosdb show --name <account> -g <rg> --query id -o tsv)

az cosmosdb sql role assignment create \
  --account-name <account> \
  --resource-group <rg> \
  --role-definition-name "Cosmos DB Built-in Data Contributor" \
  --principal-id "$PRINCIPAL_ID" \
  --scope "$COSMOS_RESOURCE_ID"
```

### SDK Authentication

```python
# Python
from azure.identity import DefaultAzureCredential
from azure.cosmos import CosmosClient

credential = DefaultAzureCredential()
client = CosmosClient(url="https://<account>.documents.azure.com:443/", credential=credential)
database = client.get_database_client("<database>")
container = database.get_container_client("<container>")
```

```typescript
// TypeScript
import { DefaultAzureCredential } from "@azure/identity";
import { CosmosClient } from "@azure/cosmos";

const credential = new DefaultAzureCredential();
const client = new CosmosClient({
  endpoint: "https://<account>.documents.azure.com:443/",
  aadCredentials: credential,
});
```

```go
// Go
import (
    "github.com/Azure/azure-sdk-for-go/sdk/azidentity"
    "github.com/Azure/azure-sdk-for-go/sdk/data/azcosmos"
)

credential, _ := azidentity.NewDefaultAzureCredential(nil)
client, _ := azcosmos.NewClient("https://<account>.documents.azure.com:443/", credential, nil)
```

---

## Query Patterns

```sql
-- Always filter by partition key first
SELECT * FROM c WHERE c.tenantId = "tenant-A" AND c.status = "active"

-- Avoid cross-partition queries (no partition key in WHERE)
-- Bad: SELECT * FROM c WHERE c.status = "active"

-- Use continuation tokens for pagination (never OFFSET/LIMIT for large result sets)
-- Continuation token is returned in the response headers / SDK response object

-- Point reads are fastest — use when you have both id and partition key
-- SDK: container.read_item(item="id", partition_key="partitionKey")
```

---

## SDK Error Handling

```python
# Python
from azure.cosmos.exceptions import CosmosHttpResponseError

try:
    item = container.read_item(item="123", partition_key="tenant-A")
except CosmosHttpResponseError as e:
    if e.status_code == 404:
        # Not found
        pass
    elif e.status_code == 429:
        # Request throttled — Cosmos SDK retries automatically by default
        # Check e.response.headers["x-ms-retry-after-ms"]
        pass
    else:
        raise
```

```go
// Go
import "github.com/Azure/azure-sdk-for-go/sdk/azcore"

_, err := container.ReadItem(ctx, azcosmos.NewPartitionKeyString("tenant-A"), "123", nil)
if err != nil {
    var respErr *azcore.ResponseError
    if errors.As(err, &respErr) {
        switch respErr.StatusCode {
        case 404:
            // Not found
        case 429:
            // Throttled — SDK retries by default; log and surface to caller
        }
    }
}
```

---

## Anti-Patterns

- **Low-cardinality partition keys** (`type`, `status`, `country`) — creates hot partitions under load.
- **Using primary/secondary account keys in application code** — use RBAC and Managed Identity.
- **`SELECT *` with no partition key filter** — forces cross-partition fan-out, slow and expensive.
- **Using OFFSET/LIMIT for deep pagination** — Cosmos does not support efficient deep offset pagination; use continuation tokens.
- **Setting `Strong` consistency globally** without measuring the latency cost — `Session` is sufficient for 99% of use cases.
- **Storing large blobs in Cosmos documents** — max 2MB per document; store large payloads in Blob Storage and reference them by URL.
- **Not setting TTL on time-bounded data** — enable TTL at container level for audit logs, session data, and temporary records to avoid unbounded growth.

---

## Cost Optimization

- **Request Unit (RU) budget per operation:** Point reads are ~1 RU; cross-partition queries can be 100s of RUs.
- Enable **autoscale** for unpredictable workloads; use **provisioned throughput** for steady-state workloads.
- **Analytical store** (Synapse Link): Enable for reporting queries to avoid RU cost on OLAP queries — they run against a column store, not the transactional store.
- Monitor RU consumption with Azure Monitor: `CRUDOperations` and `MongoOperations` metrics in the `Microsoft.DocumentDB/databaseAccounts` namespace.
