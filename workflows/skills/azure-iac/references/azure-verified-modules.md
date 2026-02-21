# Azure Verified Modules (AVM) Reference

## What Are Azure Verified Modules?

Azure Verified Modules (AVM) are Microsoft-curated Bicep (and Terraform) modules hosted at `aka.ms/AVM`. They:
- Follow consistent design principles and interface standards
- Are tested against Azure policies
- Receive ongoing maintenance from Microsoft and the community
- Cover the most common Azure resource types

**Registry:** `br/public:avm/res/<provider>/<resource-type>:<version>`

## Discovering Modules

```bash
# Browse at: https://aka.ms/AVM

# Search via Azure CLI (preview)
az bicep registry list --registry mcr.microsoft.com

# Or browse: https://github.com/Azure/bicep-registry-modules
```

## Using AVM Modules

```bicep
// Reference a module from the public registry
module storageAccount 'br/public:avm/res/storage/storage-account:0.9.0' = {
  name: 'storageAccountDeployment'
  params: {
    name: storageAccountName
    location: location
    skuName: 'Standard_LRS'
    // AVM modules use consistent parameter naming
  }
}

// Consume module outputs
output storageId string = storageAccount.outputs.resourceId
```

## Common AVM Modules

| Module Path | Resource Type | Key Features |
|------------|--------------|-------------|
| `avm/res/storage/storage-account` | Storage Account | RBAC, encryption, private endpoints |
| `avm/res/network/virtual-network` | VNet + subnets | NSG, route tables, peering |
| `avm/res/compute/virtual-machine` | VM | Managed identity, boot diags, monitoring |
| `avm/res/key-vault/vault` | Key Vault | RBAC, private endpoints, purge protection |
| `avm/res/app/container-app` | Container App | Dapr, scaling, managed identity |
| `avm/res/web/site` | App Service | Slots, monitoring, identity |
| `avm/res/sql/server` | SQL Server | Azure AD auth, auditing, TDE |
| `avm/res/container-registry/registry` | Container Registry | Geo-replication, private endpoints |
| `avm/res/operational-insights/workspace` | Log Analytics | Data retention, solutions |

## AVM Interface Standards

AVM modules follow a consistent parameter interface:

```bicep
// Standard AVM parameters (present in most modules)
param name string              // Resource name
param location string          // Azure region
param tags object = {}         // Resource tags
param enableTelemetry bool = true  // MS usage telemetry (can disable)
param lock object = {}         // Resource locks
param managedIdentities object = {}  // Managed identity config
param diagnosticSettings array = []  // Diagnostic settings
param roleAssignments array = []     // RBAC role assignments
param privateEndpoints array = []    // Private endpoint config
```

## Version Pinning

Always pin AVM module versions:
```bicep
// Pinned version — safe
module storage 'br/public:avm/res/storage/storage-account:0.9.0' = { ... }

// No version — unsafe, changes without warning
// module storage 'br/public:avm/res/storage/storage-account' = { ... }  // WRONG
```

Check for new versions at: `https://github.com/Azure/bicep-registry-modules/releases`

## Pattern AVM Modules (Multi-Resource)

Pattern modules deploy multiple resources for a common architecture:

```bicep
// Hub-spoke network topology
module hubSpoke 'br/public:avm/ptn/network/hub-networking:0.1.0' = {
  name: 'hubNetworkDeployment'
  params: {
    hubVirtualNetworks: {
      hub: {
        name: 'my-hub-vnet'
        addressPrefixes: ['10.0.0.0/16']
        location: location
      }
    }
  }
}
```

## Using AVM with Private Registry

For organizations that want to vet and host approved modules:

```bash
# Copy public module to private registry
az bicep publish \
  --file main.bicep \
  --target br:myregistry.azurecr.io/bicep/modules/storage-account:1.0.0

# Reference private registry module
// In bicepconfig.json:
{
  "moduleAliases": {
    "br": {
      "myorg": {
        "registry": "myregistry.azurecr.io",
        "modulePath": "bicep/modules"
      }
    }
  }
}

// In Bicep:
module storage 'br/myorg:storage-account:1.0.0' = { ... }
```

## bicepconfig.json

Configure registry aliases and linting rules:

```json
{
  "moduleAliases": {
    "br": {
      "public": {
        "registry": "mcr.microsoft.com",
        "modulePath": "bicep/avm"
      }
    }
  },
  "analyzers": {
    "core": {
      "enabled": true,
      "rules": {
        "no-hardcoded-env-urls": { "level": "warning" },
        "no-unused-params": { "level": "warning" },
        "no-unused-vars": { "level": "warning" },
        "prefer-interpolation": { "level": "warning" },
        "secure-parameter-default": { "level": "error" }
      }
    }
  }
}
```
