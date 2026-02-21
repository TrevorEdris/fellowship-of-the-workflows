# ARM JSON to Bicep Migration Guide

## Why Migrate from ARM to Bicep

- Cleaner syntax: 40-60% fewer lines for equivalent templates
- Type safety and IntelliSense in VS Code with Bicep extension
- Module system for code reuse
- Compile-time validation catches errors before deployment
- Parameter decorators (`@allowed`, `@secure`, `@minLength`) inline with declarations

Bicep compiles to ARM JSON — zero runtime overhead, identical deployment behavior.

## Decompile Existing ARM JSON

```bash
# Decompile ARM JSON to Bicep
az bicep decompile --file azuredeploy.json

# Output: azuredeploy.bicep (same directory)

# Validate the decompiled output
az bicep build --file azuredeploy.bicep

# Validate against a resource group
az deployment group validate \
  --resource-group my-rg \
  --template-file azuredeploy.bicep
```

**Limitation:** Decompilation is imperfect. Manual review is always required.

## Common Conversion Patterns

### Variables / Parameters

```json
// ARM JSON
"parameters": {
  "storageAccountName": {
    "type": "string",
    "metadata": { "description": "Name of the storage account" }
  }
},
"variables": {
  "location": "[resourceGroup().location]"
}
```

```bicep
// Bicep
@description('Name of the storage account')
param storageAccountName string

var location = resourceGroup().location
```

### String Concatenation

```json
// ARM JSON — concat function
"[concat(parameters('prefix'), '-', variables('uniqueSuffix'))]"

// ARM JSON — format function
"[format('{0}-{1}', parameters('prefix'), variables('suffix'))]"
```

```bicep
// Bicep — string interpolation
'${prefix}-${uniqueSuffix}'
```

### Conditions

```json
// ARM JSON
"condition": "[equals(parameters('environment'), 'prod')]"
```

```bicep
// Bicep
if environment == 'prod'
```

### Resource Dependencies

```json
// ARM JSON — explicit dependsOn required
"dependsOn": ["[resourceId('Microsoft.Storage/storageAccounts', variables('storageName'))]"]
```

```bicep
// Bicep — symbolic reference creates implicit dependency
// Just reference the resource symbol — dependsOn is automatic
resource blobService 'Microsoft.Storage/storageAccounts/blobServices@2023-01-01' = {
  parent: storageAccount  // Implicit dependency on storageAccount
  name: 'default'
}
```

### Resource References

```json
// ARM JSON — resourceId function
"[resourceId('Microsoft.Storage/storageAccounts', parameters('storageAccountName'))]"

// ARM JSON — reference function for properties
"[reference(resourceId('Microsoft.Storage/storageAccounts', variables('storageAccountName'))).primaryEndpoints.blob]"
```

```bicep
// Bicep — symbolic access
storageAccount.id                                    // resourceId equivalent
storageAccount.properties.primaryEndpoints.blob      // reference equivalent
```

### Nested Resources

```json
// ARM JSON — must specify full type and name
{
  "type": "Microsoft.Storage/storageAccounts/blobServices",
  "name": "[concat(variables('storageName'), '/default')]",
  "dependsOn": ["[variables('storageName')]"]
}
```

```bicep
// Bicep — parent property
resource blobService 'Microsoft.Storage/storageAccounts/blobServices@2023-01-01' = {
  parent: storageAccount
  name: 'default'
}
```

### Copy Loops

```json
// ARM JSON — copy element
"copy": {
  "name": "subnetCopy",
  "count": "[length(parameters('subnets'))]"
}
```

```bicep
// Bicep — for loop
resource subnets 'Microsoft.Network/virtualNetworks/subnets@2023-09-01' = [for subnet in subnets: {
  parent: vnet
  name: subnet.name
  properties: { addressPrefix: subnet.addressPrefix }
}]
```

## Manual Fixes After Decompilation

The decompiler commonly produces these patterns requiring manual cleanup:

1. **`dependsOn` arrays** — Replace with symbolic references where possible
2. **`concat()` calls** — Replace with Bicep string interpolation
3. **Nested resource names** — Move `name` to `parent` property
4. **Missing `@description()` decorators** — Add to all parameters
5. **`[variables('x')]` patterns** — Simplify to `varName` reference
6. **Hardcoded API versions** — Verify against current Azure docs (versions get deprecated)
7. **`[resourceGroup().location]`** — Simplify to `resourceGroup().location` (no brackets needed in Bicep)

## Incremental Migration Strategy

For large templates, migrate module by module:

1. Identify logical groupings (networking, storage, compute)
2. Extract each group into a Bicep module
3. Create a `main.bicep` that orchestrates the modules
4. Validate each module independently before wiring together
5. Use `az deployment group what-if` to confirm parity before replacing ARM deployments

## Validate Parity

```bash
# Export current ARM template from deployed resource group
az group export --name my-rg --output-format json > current.json

# Build new Bicep to ARM
az bicep build --file main.bicep --outfile new.json

# Diff (jq helps normalize)
diff <(jq --sort-keys . current.json) <(jq --sort-keys . new.json)
```
