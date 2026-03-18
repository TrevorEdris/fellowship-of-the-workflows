# Bicep Patterns Reference

## Template Structure

```bicep
// Metadata (optional but recommended)
metadata description = 'Storage account for application data'
metadata author = 'platform-team'

// Target scope (defaults to resourceGroup)
targetScope = 'resourceGroup' // resourceGroup | subscription | managementGroup | tenant

// ---------------------------------------------------------------------------
// Parameters
// ---------------------------------------------------------------------------
@description('Deployment environment')
@allowed(['dev', 'staging', 'prod'])
param environment string = 'dev'

@description('Azure region for resources')
param location string = resourceGroup().location

@description('Storage account SKU')
@allowed(['Standard_LRS', 'Standard_GRS', 'Standard_ZRS', 'Premium_LRS'])
param storageSkuName string = 'Standard_LRS'

// Secure parameters — never logged or echoed
@description('Database administrator password')
@secure()
param adminPassword string

// ---------------------------------------------------------------------------
// Variables
// ---------------------------------------------------------------------------
var storageAccountName = 'st${environment}${uniqueString(resourceGroup().id)}'
var isProd = environment == 'prod'
var storageSku = isProd ? 'Standard_GRS' : storageSkuName

// ---------------------------------------------------------------------------
// Resources
// ---------------------------------------------------------------------------
resource storageAccount 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: storageAccountName
  location: location
  kind: 'StorageV2'
  sku: {
    name: storageSku
  }
  properties: {
    accessTier: 'Hot'
    minimumTlsVersion: 'TLS1_2'
    supportsHttpsTrafficOnly: true
    allowBlobPublicAccess: false
    networkAcls: {
      defaultAction: 'Deny'
      bypass: 'AzureServices'
    }
    encryption: {
      services: {
        blob: { enabled: true }
        file: { enabled: true }
      }
      keySource: 'Microsoft.Storage'
    }
  }
}

// ---------------------------------------------------------------------------
// Outputs
// ---------------------------------------------------------------------------
output storageAccountId string = storageAccount.id
output storageAccountName string = storageAccount.name
output primaryEndpoint string = storageAccount.properties.primaryEndpoints.blob
```

## Decorators

```bicep
// String validation
@minLength(3)
@maxLength(24)
param storageAccountName string

// Numeric range
@minValue(1)
@maxValue(10)
param instanceCount int = 2

// Description (always add for all parameters)
@description('The name of the resource')
param resourceName string

// Allowed values
@allowed(['Basic', 'Standard', 'Premium'])
param tier string

// Secure (never logged, encrypted in state)
@secure()
param connectionString string

// Metadata (additional documentation)
@metadata({
  example: 'myapp'
  notes: 'Must be globally unique'
})
param appName string
```

## Conditions and Loops

```bicep
// Conditional resource deployment
resource diagnosticSettings 'Microsoft.Insights/diagnosticSettings@2021-05-01-preview' = if (isProd) {
  name: 'diag-${resourceName}'
  scope: storageAccount
  properties: {
    workspaceId: logAnalyticsWorkspaceId
    logs: [{ category: 'StorageRead'; enabled: true }]
    metrics: [{ category: 'Transaction'; enabled: true }]
  }
}

// Loop over array
param subnetConfigs array = [
  { name: 'web'; prefix: '10.0.0.0/24' }
  { name: 'app'; prefix: '10.0.1.0/24' }
  { name: 'data'; prefix: '10.0.2.0/24' }
]

resource subnets 'Microsoft.Network/virtualNetworks/subnets@2023-09-01' = [for subnet in subnetConfigs: {
  name: subnet.name
  parent: vnet
  properties: {
    addressPrefix: subnet.prefix
  }
}]

// Loop with index
resource storageContainers 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-01-01' = [for i in range(0, 3): {
  name: 'container-${i}'
  parent: blobServices
}]
```

## Modules

```bicep
// Define a reusable module: modules/storage.bicep
// Call the module from main.bicep

module appStorage './modules/storage.bicep' = {
  name: 'appStorageDeployment'
  params: {
    environment: environment
    location: location
    storageSkuName: 'Standard_GRS'
  }
}

// Consume module outputs
output storageId string = appStorage.outputs.storageAccountId

// Nested module
module networking './modules/networking.bicep' = {
  name: 'networkingDeployment'
  scope: resourceGroup('my-network-rg')  // Deploy to different RG
  params: {
    vnetName: 'my-vnet'
    location: location
  }
}
```

## Existing Resources (References)

```bicep
// Reference an existing resource without managing it
resource existingKeyVault 'Microsoft.KeyVault/vaults@2023-07-01' existing = {
  name: 'my-keyvault-name'
  scope: resourceGroup('my-keyvault-rg')
}

// Use the existing resource
resource secret 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: existingKeyVault
  name: 'my-secret'
  properties: {
    value: adminPassword
  }
}
```

## String Functions

```bicep
// uniqueString — deterministic hash based on input
var uniqueSuffix = uniqueString(resourceGroup().id)
var storageName = 'st${uniqueSuffix}'  // 'stgfhj3k2m1...' (13 chars max)

// concat / string interpolation
var fullName = '${prefix}-${environment}-${uniqueSuffix}'

// toLower — storage accounts require lowercase
var lowerName = toLower(storageName)

// substring
var shortName = substring(uniqueString(resourceGroup().id), 0, 8)
```

## What-If Deployment

```bash
# Resource group scope
az deployment group what-if \
  --resource-group my-rg \
  --template-file main.bicep \
  --parameters environment=prod location=eastus

# Using parameter files (.bicepparam)
az deployment group what-if \
  --resource-group my-rg \
  --template-file main.bicep \
  --parameters @main.prod.bicepparam

# Subscription scope
az deployment sub what-if \
  --location eastus \
  --template-file subscription-level.bicep
```

## .bicepparam Files (Bicep 0.18+)

```bicep
// main.prod.bicepparam
using 'main.bicep'

param environment = 'prod'
param location = 'eastus'
param storageSkuName = 'Standard_GRS'
```

## Build and Validate

```bash
# Compile Bicep to ARM JSON
az bicep build --file main.bicep --outfile main.json

# Validate template (no deployment)
az deployment group validate \
  --resource-group my-rg \
  --template-file main.bicep \
  --parameters environment=dev

# Lint (built-in)
az bicep lint --file main.bicep
```
