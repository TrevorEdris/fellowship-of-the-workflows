---
name: azure-iac
description: "Author, review, and deploy Azure infrastructure using Bicep or ARM templates. Covers Bicep modules, what-if deployments, ARM decompilation, and Azure Verified Modules. Use for any Azure-native IaC task."
context: fork
allowed-tools: Bash, Read, Glob, Grep, Write
model: sonnet
argument-hint: "[generate|review|whatif|security|migrate]"
user-invocable: true
tags: [azure, infrastructure]
---

# Azure IaC

Author, review, and deploy Azure infrastructure using Bicep and ARM templates.

---

## When to Use

- Writing Bicep templates for Azure resource provisioning
- Reviewing Bicep modules for correctness and anti-patterns
- Running `what-if` deployments to preview changes before applying
- Converting legacy ARM JSON to Bicep (`az bicep decompile`)
- Discovering and applying Azure Verified Modules from the registry
- Auditing templates with PSRule for Azure compliance checks

**Out of scope:** CI/CD pipeline definition (use `/cicd-pipeline`), multi-cloud or Terraform-based Azure configs (use `/terraform`), Azure Kubernetes Service cluster management.

**Note:** No dedicated Bicep MCP server exists as of early 2026. The Azure MCP (`azure-mcp`) covers ARM resource operations but not template generation. This skill operates via CLI tools.

---

## Quick Start

```
/azure-iac generate    # Scaffold Bicep template for specified resources
/azure-iac review      # Review existing Bicep/ARM for correctness and anti-patterns
/azure-iac whatif      # Preview deployment changes with az deployment what-if
/azure-iac security    # Run PSRule for Azure compliance scanning
/azure-iac migrate     # Convert ARM JSON to Bicep using az bicep decompile
```

No argument? Detects `*.bicep` or ARM JSON files; defaults to `review` if templates exist, `generate` if not.

---

## Context

BICEP/ARM FILES:
```
!`find . -maxdepth 4 \( -name "*.bicep" -o -name "*.bicepparam" \) 2>/dev/null | head -20; find . -maxdepth 3 -name "azuredeploy.json" -o -name "mainTemplate.json" 2>/dev/null | head -10`
```

AZURE CLI:
```
!`az account show --query "{subscription:name,id:id}" 2>/dev/null || echo "Not logged in to Azure CLI"`
```

BICEP VERSION:
```
!`az bicep version 2>/dev/null || echo "az bicep not installed"`
```

---

## Mode: generate

Scaffold a Bicep template for specified Azure resources.

**Template structure:**
```bicep
// Standard Bicep file header
@description('Deployment environment name')
param environment string

@description('Azure region for resources')
param location string = resourceGroup().location

var prefix = '${environment}-${uniqueString(resourceGroup().id)}'

// Resources section
resource <name> '<type>@<api-version>' = {
  name: <name>
  location: location
  properties: { ... }
}

// Outputs
output resourceId string = <name>.id
```

**Steps:**
1. Gather: resource type(s), environment strategy, naming convention
2. Apply `@description()` decorator to all parameters
3. Use `uniqueString(resourceGroup().id)` for globally unique names
4. Set `location` parameter with `resourceGroup().location` default
5. Add `@allowed()` decorators for enum-like parameters
6. Use Bicep modules for reusable components
7. Add Outputs for values needed by other deployments or pipelines

**Common resource API versions (verify current at docs.microsoft.com):**
- Storage accounts: `Microsoft.Storage/storageAccounts@2023-01-01`
- App Service Plan: `Microsoft.Web/serverfarms@2023-01-01`
- Web App: `Microsoft.Web/sites@2023-01-01`
- Key Vault: `Microsoft.KeyVault/vaults@2023-07-01`
- Container Registry: `Microsoft.ContainerRegistry/registries@2023-07-01`

Asset template: `assets/bicep-skeleton.bicep`

---

## Mode: review

Review existing Bicep/ARM templates for correctness and anti-patterns.

**Anti-patterns to flag:**

| Anti-Pattern | Severity | Correction |
|-------------|----------|-----------|
| Hardcoded storage account names (globally unique required) | High | Use `uniqueString(resourceGroup().id)` |
| Missing `@description()` on parameters | Medium | Add descriptive decorator to all params |
| `storageProfile.osDisk.createOption` without `ManagedDisk` | High | Use managed disks |
| Secrets in `parameters` without `@secure()` | Critical | Add `@secure()` decorator |
| ARM JSON when Bicep is available | Low | Migrate to Bicep |
| Missing `dependsOn` for implicit dependencies | High | Use symbolic references (Bicep auto-handles) |
| Cross-scope deployments without explicit `scope` | Medium | Use `targetScope` declaration |
| Template size > 4MB | High | Split into modules |

**Triage levels:**
- **[CRITICAL]**: `@secure()` missing on passwords/keys, missing resource locks on prod
- **[HIGH]**: Hardcoded values, missing module extraction for repeated patterns
- **[LOW]**: Missing descriptions, verbose expressions that could use variables

---

## Mode: whatif

Preview deployment changes before applying.

**Steps:**
1. Construct `az deployment group what-if` command with correct scope
2. Parse output to summarize: Create / Modify / Delete / Ignore / NoEffect / Unsupported
3. **Flag deletions** — require explicit acknowledgment
4. **Flag stateful resource modifications** (storage accounts, databases, Key Vaults)
5. Provide the apply command for confirmed deployments

**What-if commands by scope:**

```bash
# Resource group scope (most common)
az deployment group what-if \
  --resource-group <rg-name> \
  --template-file main.bicep \
  --parameters environment=prod

# Subscription scope
az deployment sub what-if \
  --location eastus \
  --template-file main.bicep

# Using .bicepparam files
az deployment group what-if \
  --resource-group <rg-name> \
  --template-file main.bicep \
  --parameters @main.prod.bicepparam
```

---

## Mode: security

Run PSRule for Azure compliance scanning.

**Steps:**
1. Install PSRule: `Install-Module PSRule.Rules.Azure -Scope CurrentUser`
2. Run against Bicep files: `Invoke-PSRule -InputPath . -Module PSRule.Rules.Azure`
3. Common rule sets:
   - `Azure.Storage.*` — Storage account security (HTTPS, TLS version, blob public access)
   - `Azure.KeyVault.*` — Key Vault access policies, purge protection, soft delete
   - `Azure.Web.*` — App Service TLS, managed identity, always-on
   - `Azure.SQL.*` — SQL auditing, transparent data encryption, firewall rules
4. Suppress intentional deviations with `ps-rule.yaml` suppression rules with documented rationale

---

## Mode: migrate

Convert ARM JSON templates to Bicep.

**Steps:**
1. Run `az bicep decompile --file <template.json>`
2. Review decompiled output — decompilation is imperfect:
   - Nested resources may need manual restructuring
   - `dependsOn` arrays should be replaced with symbolic references
   - `concat()` calls can be replaced with string interpolation
   - Hardcoded API versions should be verified against current docs
3. Extract repeated patterns into `modules/` subdirectory
4. Add `@description()` decorators to all parameters (decompiler omits these)
5. Validate with `az bicep build --file main.bicep`

---

## Key References

| Reference | Contents |
|-----------|----------|
| `references/bicep-patterns.md` | Modules, decorators, what-if, string interpolation, loops |
| `references/arm-to-bicep.md` | Decompile guide, common conversion patterns, manual fixes |
| `references/azure-verified-modules.md` | Module registry, discovering and consuming AVM modules |

## Asset Templates

| Asset | Purpose |
|-------|---------|
| `assets/bicep-skeleton.bicep` | Starter Bicep template with common sections |
