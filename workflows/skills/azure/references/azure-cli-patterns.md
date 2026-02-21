# Azure CLI Patterns

Covers `az`, `azd`, and Bicep CLI patterns for day-to-day Azure development and CI/CD pipelines.

---

## Azure CLI (`az`)

### Installation and Authentication

```bash
# macOS
brew install azure-cli

# Linux (Debian/Ubuntu)
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash

# Authenticate
az login                          # Interactive browser
az login --use-device-code        # Headless / SSH
az login --tenant <tenant-id>     # Specific tenant

# Verify
az account show
```

### Subscription Management

```bash
# List all subscriptions you have access to
az account list --output table

# Switch subscriptions
az account set --subscription "<subscription-name-or-id>"

# Show current subscription
az account show --query "{name:name, id:id, tenant:tenantId}" --output table

# Set default resource group and location to avoid repeating flags
az config set defaults.group=<resource-group> defaults.location=eastus

# Clear defaults
az config unset defaults.group defaults.location
```

### Common Resource Patterns

```bash
# List resource groups
az group list --output table

# Create a resource group
az group create --name <rg> --location eastus

# List all resources in a resource group
az resource list --resource-group <rg> --output table

# Get resource details
az resource show \
  --resource-group <rg> \
  --resource-type "Microsoft.Storage/storageAccounts" \
  --name <account-name>

# Delete a resource group (and all resources in it)
az group delete --name <rg> --yes --no-wait
```

### Output Formatting

```bash
# Table (human-readable)
az resource list --resource-group <rg> --output table

# JSON (default — scriptable)
az account show --output json

# YAML
az resource list --output yaml

# TSV (for shell scripting)
az account show --query name --output tsv

# JMESPath queries
az vm list --query "[].{name:name, os:storageProfile.osDisk.osType}" --output table
```

---

## OIDC for CI/CD Pipelines

Use OIDC federated credentials instead of long-lived client secrets in CI/CD. The pipeline exchanges a short-lived OIDC token for an Azure access token — no secret to store or rotate.

### GitHub Actions Setup

**Step 1: Create federated credential on a service principal or managed identity**

```bash
# Create an app registration (if using service principal)
APP_ID=$(az ad app create --display-name "<app-name>" --query appId -o tsv)
SP_ID=$(az ad sp create --id "$APP_ID" --query id -o tsv)

# Add federated credential for the GitHub repo's main branch
az ad app federated-credential create \
  --id "$APP_ID" \
  --parameters '{
    "name": "github-main",
    "issuer": "https://token.actions.githubusercontent.com",
    "subject": "repo:<org>/<repo>:ref:refs/heads/main",
    "audiences": ["api://AzureADTokenExchange"]
  }'

# Also add for pull requests if needed
az ad app federated-credential create \
  --id "$APP_ID" \
  --parameters '{
    "name": "github-prs",
    "issuer": "https://token.actions.githubusercontent.com",
    "subject": "repo:<org>/<repo>:pull_request",
    "audiences": ["api://AzureADTokenExchange"]
  }'

# Assign a role to the service principal
az role assignment create \
  --assignee "$SP_ID" \
  --role "Contributor" \
  --scope /subscriptions/<subscription-id>/resourceGroups/<rg>
```

**Step 2: GitHub Actions workflow**

```yaml
permissions:
  id-token: write
  contents: read

steps:
  - uses: azure/login@v2
    with:
      client-id: ${{ secrets.AZURE_CLIENT_ID }}
      tenant-id: ${{ secrets.AZURE_TENANT_ID }}
      subscription-id: ${{ secrets.AZURE_SUBSCRIPTION_ID }}
      # No client-secret — OIDC handles auth

  - name: Deploy
    run: az webapp deploy ...
```

**GitHub Actions secrets to set** (not client-secret):
- `AZURE_CLIENT_ID` — the app registration client ID
- `AZURE_TENANT_ID` — your Entra ID tenant ID
- `AZURE_SUBSCRIPTION_ID` — target subscription ID

### Azure DevOps Setup

Use a **Workload Identity Federation** service connection (ADO 2023+):

1. Project Settings → Service connections → New service connection → Azure Resource Manager
2. Select **Workload Identity Federation (automatic)** — ADO creates the federated credential automatically.
3. Reference the connection in pipelines:

```yaml
- task: AzureCLI@2
  inputs:
    azureSubscription: '<service-connection-name>'
    scriptType: 'bash'
    scriptLocation: 'inlineScript'
    inlineScript: |
      az account show
      az webapp deploy ...
```

---

## Azure Developer CLI (`azd`)

`azd` provides an opinionated end-to-end developer workflow: init → provision (Bicep/Terraform) → deploy → monitor → teardown.

```bash
# Install
brew install azure-developer-cli  # macOS
winget install Microsoft.Azd      # Windows

# Authenticate
azd auth login

# Initialize a new project (creates azure.yaml + infra/ templates)
azd init

# Provision infrastructure + deploy application
azd up

# Deploy only (assumes infra already provisioned)
azd deploy

# Tear down all provisioned resources
azd down

# Manage environments (dev, staging, prod)
azd env new staging
azd env select staging
azd env list
```

**`azure.yaml` structure:**

```yaml
name: my-app
services:
  api:
    project: ./src/api
    language: go
    host: appservice
  worker:
    project: ./src/worker
    language: python
    host: containerapp
```

`azd` integrates with GitHub Actions via `azure/azd-action` and with Azure Pipelines via the ADO extension.

---

## Bicep CLI

Bicep compiles to ARM JSON. The CLI is bundled with `az` but can also be managed separately.

```bash
# Verify Bicep is installed
az bicep version

# Upgrade to latest
az bicep upgrade

# Compile Bicep → ARM JSON
az bicep build --file main.bicep

# Decompile ARM JSON → Bicep (for migrating existing ARM templates)
az bicep decompile --file template.json

# Validate a Bicep file without deploying
az deployment group validate \
  --resource-group <rg> \
  --template-file main.bicep \
  --parameters @main.parameters.json

# What-if (dry run — show what would change)
az deployment group what-if \
  --resource-group <rg> \
  --template-file main.bicep \
  --parameters @main.parameters.json

# Deploy
az deployment group create \
  --resource-group <rg> \
  --template-file main.bicep \
  --parameters @main.parameters.json \
  --name deploy-$(date +%Y%m%d%H%M%S)
```

---

## MFA and Security Notes

- **As of October 2025:** MFA is mandatory for all write operations via Azure CLI in interactive sessions.
- **Headless environments:** Use `az login --use-device-code` to complete MFA on another device, or use OIDC federated credentials to bypass interactive auth entirely.
- **Service Principal with secret (legacy):** If you must use a secret, set `AZURE_CLIENT_SECRET`, `AZURE_CLIENT_ID`, and `AZURE_TENANT_ID` — do not embed in scripts. Rotate secrets every 90 days maximum.
- **Token expiry:** Azure CLI tokens expire after 60–70 minutes. Long-running scripts should use `az account get-access-token --query accessToken` to refresh tokens programmatically.
