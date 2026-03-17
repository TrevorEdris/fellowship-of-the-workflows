# IaC Decision Guide: Bicep vs Terraform for Azure

---

## Decision Tree

```
Working exclusively with Azure?
  YES → Small/new team or Azure-native shop?
    YES → Bicep
           - No state management overhead
           - Native Azure preview support (new services land in Bicep before Terraform)
           - Simpler syntax, first-class Azure tooling
    NO  → Already using Terraform elsewhere in the org?
      YES → Terraform (azurerm provider)
             - Consistent tooling and CI/CD pipelines across teams
             - Reuse existing modules and state management patterns
      NO  → Bicep (recommended for Azure-only organizations)
  NO (multi-cloud, SaaS providers, on-prem) → Terraform
  Have existing ARM templates? → Decompile first:
    az bicep decompile --file template.json
```

---

## Comparison

| Dimension | Bicep | Terraform |
|-----------|-------|-----------|
| State management | None — Azure tracks deployments server-side | Required — use Azure Storage backend |
| Language | Domain-specific (Azure-native) | HCL (HashiCorp Configuration Language) |
| New Azure service support | Same day as ARM API (Bicep compiles to ARM) | Provider update required (days to weeks lag) |
| Multi-cloud | Azure only | AWS, GCP, Azure, Kubernetes, SaaS providers |
| Modules | Bicep modules + Azure Verified Modules (AVM) | Terraform Registry modules |
| IDE support | VS Code Bicep extension (excellent) | HashiCorp Sentinel / Terraform extension |
| CI/CD | `az deployment group create` or `azd up` | `terraform plan` + `terraform apply` |
| Rollback | Redeploy previous template version | `terraform apply` with previous state |
| Drift detection | `az deployment group what-if` | `terraform plan` (shows drift from state) |

---

## Bicep Patterns

### Module Structure

```
infra/
├── main.bicep           # Entry point — orchestrates modules
├── main.bicepparam      # Parameters file (Bicep 0.18+)
├── modules/
│   ├── storage.bicep
│   ├── keyvault.bicep
│   └── appservice.bicep
└── abbreviations.json   # Naming convention reference
```

### Naming and Parameter Pattern

```bicep
// main.bicep
@description('Primary Azure region for all resources')
param location string = resourceGroup().location

@description('Environment name: dev, staging, prod')
@allowed(['dev', 'staging', 'prod'])
param environment string

var prefix = 'myapp-${environment}'

module storage 'modules/storage.bicep' = {
  name: 'deploy-storage'
  params: {
    location: location
    storageAccountName: '${replace(prefix, '-', '')}sa'
  }
}
```

### Key Vault with Access via RBAC

```bicep
resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: '${prefix}-kv'
  location: location
  properties: {
    sku: {
      family: 'A'
      name: 'standard'
    }
    tenantId: subscription().tenantId
    enableRbacAuthorization: true   // Use RBAC, not access policies
    enableSoftDelete: true
    softDeleteRetentionInDays: 7
    enablePurgeProtection: true     // Required for production
  }
}

// Assign Key Vault Secrets User to a managed identity
resource kvSecretUserRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(keyVault.id, managedIdentity.id, 'Key Vault Secrets User')
  scope: keyVault
  properties: {
    roleDefinitionId: subscriptionResourceId(
      'Microsoft.Authorization/roleDefinitions',
      '4633458b-17de-408a-b874-0445c86b69e6'  // Key Vault Secrets User
    )
    principalId: managedIdentity.properties.principalId
    principalType: 'ServicePrincipal'
  }
}
```

### What-If Before Deploy

```bash
# Dry run — shows create, modify, delete, no-change per resource
az deployment group what-if \
  --resource-group <rg> \
  --template-file infra/main.bicep \
  --parameters infra/main.bicepparam
```

---

## Terraform Patterns

### Backend Configuration (Azure Storage)

```hcl
# backend.tf
terraform {
  backend "azurerm" {
    resource_group_name  = "tfstate-rg"
    storage_account_name = "tfstatemyorg"
    container_name       = "tfstate"
    key                  = "myapp/prod.tfstate"
  }
}
```

```bash
# Bootstrap the state storage account (one-time)
az group create --name tfstate-rg --location eastus
az storage account create --name tfstatemyorg -g tfstate-rg \
  --sku Standard_LRS --kind StorageV2
az storage container create --name tfstate \
  --account-name tfstatemyorg
```

### Provider and Auth

```hcl
# providers.tf
terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.90"  # Pin to minor version
    }
  }
  required_version = ">= 1.6"
}

provider "azurerm" {
  features {}
  # Auth: uses DefaultAzureCredential — az login or env vars
  # For CI: set ARM_CLIENT_ID, ARM_TENANT_ID, ARM_SUBSCRIPTION_ID
  # For OIDC CI: set ARM_USE_OIDC=true + ARM_OIDC_TOKEN env var
}
```

### Key Vault with RBAC (Terraform)

```hcl
resource "azurerm_key_vault" "main" {
  name                       = "${local.prefix}-kv"
  location                   = azurerm_resource_group.main.location
  resource_group_name        = azurerm_resource_group.main.name
  tenant_id                  = data.azurerm_client_config.current.tenant_id
  sku_name                   = "standard"
  enable_rbac_authorization  = true
  soft_delete_retention_days = 7
  purge_protection_enabled   = true
}

resource "azurerm_role_assignment" "kv_secrets_user" {
  scope                = azurerm_key_vault.main.id
  role_definition_name = "Key Vault Secrets User"
  principal_id         = azurerm_user_assigned_identity.main.principal_id
}
```

### CI/CD with OIDC (Terraform + GitHub Actions)

```yaml
# .github/workflows/terraform.yml
permissions:
  id-token: write
  contents: read

env:
  ARM_CLIENT_ID: ${{ secrets.AZURE_CLIENT_ID }}
  ARM_TENANT_ID: ${{ secrets.AZURE_TENANT_ID }}
  ARM_SUBSCRIPTION_ID: ${{ secrets.AZURE_SUBSCRIPTION_ID }}
  ARM_USE_OIDC: "true"

steps:
  - uses: azure/login@v2
    with:
      client-id: ${{ secrets.AZURE_CLIENT_ID }}
      tenant-id: ${{ secrets.AZURE_TENANT_ID }}
      subscription-id: ${{ secrets.AZURE_SUBSCRIPTION_ID }}

  - uses: hashicorp/setup-terraform@v3

  - run: terraform init
  - run: terraform plan -out=tfplan
  - run: terraform apply tfplan
```

---

## Azure Verified Modules (AVM)

AVM provides Microsoft-curated, tested Bicep and Terraform modules for common Azure patterns.

- Browse: https://azure.github.io/Azure-Verified-Modules/
- Bicep registry: `br/public:avm/res/<provider>/<resource>:<version>`
- Terraform registry: `Azure/avm-res-<provider>-<resource>/azurerm`

```bicep
// Example: AVM Storage Account module
module storageAccount 'br/public:avm/res/storage/storage-account:0.9.0' = {
  name: 'storageAccountDeployment'
  params: {
    name: 'mystorageaccount'
    location: location
  }
}
```
