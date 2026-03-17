// =============================================================================
// Bicep Template Skeleton
// Replace all TODO comments with your actual values.
// =============================================================================

// targetScope = 'resourceGroup'  // Default; change if deploying at subscription level

// =============================================================================
// Parameters
// =============================================================================

@description('Deployment environment name')
@allowed(['dev', 'staging', 'prod'])
param environment string = 'dev'

@description('Azure region for all resources')
param location string = resourceGroup().location

@description('Resource name prefix — used to generate resource names')
@minLength(2)
@maxLength(20)
param prefix string

// TODO: Add secure parameters with @secure() decorator
// @description('Administrator password')
// @secure()
// param adminPassword string

// =============================================================================
// Variables
// =============================================================================

// Use uniqueString for globally unique names (storage accounts, key vaults, etc.)
var uniqueSuffix = uniqueString(resourceGroup().id)
var isProd = environment == 'prod'

// Common tags applied to all resources
var commonTags = {
  Environment: environment
  Project: prefix
  ManagedBy: 'bicep'
  // Add cost center, owner, etc. per your org standards
}

// =============================================================================
// Resources
// =============================================================================

// ---------------------------------------------------------------------------
// Storage Account
// ---------------------------------------------------------------------------
resource storageAccount 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: 'st${prefix}${environment}${substring(uniqueSuffix, 0, 8)}'
  location: location
  tags: commonTags
  kind: 'StorageV2'
  sku: {
    name: isProd ? 'Standard_GRS' : 'Standard_LRS'
  }
  properties: {
    minimumTlsVersion: 'TLS1_2'
    supportsHttpsTrafficOnly: true
    allowBlobPublicAccess: false
    accessTier: 'Hot'
    encryption: {
      services: {
        blob: { enabled: true }
        file: { enabled: true }
      }
      keySource: 'Microsoft.Storage'
    }
    networkAcls: {
      defaultAction: 'Deny'
      bypass: 'AzureServices'
    }
  }
}

resource blobService 'Microsoft.Storage/storageAccounts/blobServices@2023-01-01' = {
  parent: storageAccount
  name: 'default'
  properties: {
    deleteRetentionPolicy: {
      enabled: true
      days: isProd ? 30 : 7
    }
    containerDeleteRetentionPolicy: {
      enabled: true
      days: isProd ? 30 : 7
    }
  }
}

// ---------------------------------------------------------------------------
// TODO: Add your resources here
// ---------------------------------------------------------------------------
// Example: Key Vault
// resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' = {
//   name: 'kv-${prefix}-${environment}-${substring(uniqueSuffix, 0, 6)}'
//   location: location
//   tags: commonTags
//   properties: {
//     sku: { family: 'A'; name: 'standard' }
//     tenantId: subscription().tenantId
//     enableSoftDelete: true
//     softDeleteRetentionInDays: isProd ? 90 : 7
//     enablePurgeProtection: isProd  // Required for compliance in prod
//     enableRbacAuthorization: true  // Prefer RBAC over access policies
//   }
// }

// =============================================================================
// Outputs
// =============================================================================

output storageAccountName string = storageAccount.name
output storageAccountId string = storageAccount.id
output storageAccountEndpoint string = storageAccount.properties.primaryEndpoints.blob

// Add additional outputs for values consumed by other templates or CI/CD pipelines
