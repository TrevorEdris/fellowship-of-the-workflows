# Azure Functions Deployment Patterns

---

## Hosting Plan Comparison

| Plan | Cold Start | Min Instances | Max Duration | VNet | Cost Model | Best For |
|------|-----------|--------------|-------------|------|-----------|----------|
| **Consumption** | Yes (1–30s) | 0 | 10 min | No (outbound only via NAT GW) | Pay per invocation | Infrequent, cost-sensitive, non-latency-critical |
| **Flex Consumption** | Minimal | Configurable (0–N) | 60 min | Yes | Pay per invocation + pre-warmed instances | Most new production workloads (2024+) |
| **Premium** | No | 1+ (always-ready) | 60 min | Yes | Always-on + per-execution | Latency-sensitive, VNet integration required |
| **Dedicated** (App Service Plan) | No | ASP instance count | Unlimited | Yes | Fixed (ASP cost) | Always-on, high-density, existing ASP |
| **Container Apps** | No | Configurable | Unlimited | Yes | Pay per container-second | Custom runtimes, sidecar patterns, event-driven |

**Decision guide:**
- New workload, cost-sensitive, can tolerate cold starts → **Consumption**
- New production workload, need reliability + reasonable cost → **Flex Consumption**
- Sub-second response time required, or private VNet access needed → **Premium**
- Existing App Service Plan with spare capacity → **Dedicated**
- Non-.NET/Node/Python runtime, or sidecar needed → **Container Apps**

---

## Creating a Function App

```bash
# Create storage account (required for Consumption/Flex/Premium plans)
az storage account create \
  --name <storage-account> \
  --resource-group <rg> \
  --location eastus \
  --sku Standard_LRS

# Flex Consumption (recommended for new production apps)
az functionapp create \
  --name <function-app> \
  --resource-group <rg> \
  --storage-account <storage-account> \
  --flexconsumption-location eastus \
  --runtime node \
  --runtime-version 20 \
  --functions-version 4

# Premium plan
az appservice plan create --name <plan> --resource-group <rg> --sku EP1 --is-linux
az functionapp create \
  --name <function-app> \
  --resource-group <rg> \
  --plan <plan> \
  --storage-account <storage-account> \
  --runtime node \
  --functions-version 4

# Enable Managed Identity (recommended — use instead of storage keys)
az functionapp identity assign --name <function-app> --resource-group <rg>
```

---

## Deployment Methods

### Method 1: `func azure functionapp publish` (simplest)

```bash
# Build first (TypeScript)
npm run build

# Deploy (uploads a deployment package)
func azure functionapp publish <function-app>

# Deploy with remote build (server-side dependency install)
func azure functionapp publish <function-app> --build remote
```

### Method 2: Zip Deploy via `az` CLI

```bash
# Create deployment package
zip -r build.zip . \
  --exclude "*.git*" \
  --exclude "node_modules/*" \
  --exclude "*.test.*" \
  --exclude "local.settings.json"

# Deploy
az functionapp deployment source config-zip \
  --resource-group <rg> \
  --name <function-app> \
  --src build.zip
```

### Method 3: `azd deploy` (recommended for greenfield)

```yaml
# azure.yaml
name: my-function-app
services:
  api:
    project: ./
    language: ts
    host: function
```

```bash
azd up      # Provision + deploy
azd deploy  # Deploy only (after initial provision)
```

### Method 4: GitHub Actions

```yaml
# .github/workflows/deploy-functions.yml
name: Deploy Azure Functions

on:
  push:
    branches: [main]

permissions:
  id-token: write
  contents: read

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: "20"
          cache: "npm"

      - run: npm ci && npm run build

      - uses: azure/login@v2
        with:
          client-id: ${{ secrets.AZURE_CLIENT_ID }}
          tenant-id: ${{ secrets.AZURE_TENANT_ID }}
          subscription-id: ${{ secrets.AZURE_SUBSCRIPTION_ID }}

      - uses: Azure/functions-action@v1
        with:
          app-name: ${{ vars.FUNCTION_APP_NAME }}
          package: "."
          respect-funcignore: true
```

---

## Deployment Slots

Slots allow zero-downtime deployments with instant swap-based rollback.

```bash
# Create a staging slot
az functionapp deployment slot create \
  --name <function-app> \
  --resource-group <rg> \
  --slot staging

# Configure slot-specific settings (NOT swapped — stays with slot)
az functionapp config appsettings set \
  --name <function-app> \
  --resource-group <rg> \
  --slot staging \
  --settings "SLOT_NAME=staging"

# Settings that SHOULD swap with slot (marked as slot setting = false — default)
# Settings that should NOT swap (sticky to slot — e.g., connection strings to staging resources):
az functionapp config appsettings set \
  --name <function-app> \
  --resource-group <rg> \
  --slot staging \
  --slot-settings "StagingDatabaseConnection=<staging-conn-str>"

# Deploy to staging slot
func azure functionapp publish <function-app> --slot staging

# Verify staging
curl https://<function-app>-staging.azurewebsites.net/api/health

# Swap staging → production (atomic, ~1 second)
az functionapp deployment slot swap \
  --resource-group <rg> \
  --name <function-app> \
  --slot staging \
  --target-slot production

# Rollback: swap back
az functionapp deployment slot swap \
  --resource-group <rg> \
  --name <function-app> \
  --slot production \
  --target-slot staging
```

### GitHub Actions with Slot Swap

```yaml
- name: Deploy to staging slot
  uses: Azure/functions-action@v1
  with:
    app-name: ${{ vars.FUNCTION_APP_NAME }}
    slot-name: staging
    package: "."

- name: Smoke test staging
  run: |
    curl -f "https://${{ vars.FUNCTION_APP_NAME }}-staging.azurewebsites.net/api/health"

- name: Swap to production
  run: |
    az functionapp deployment slot swap \
      --name ${{ vars.FUNCTION_APP_NAME }} \
      --resource-group ${{ vars.RESOURCE_GROUP }} \
      --slot staging \
      --target-slot production
```

---

## Environment Configuration

```bash
# Set app settings (applied immediately to running app)
az functionapp config appsettings set \
  --name <function-app> \
  --resource-group <rg> \
  --settings "KEY=value" "ANOTHER_KEY=value2"

# Use Key Vault references (preferred — avoids secrets in app settings)
az functionapp config appsettings set \
  --name <function-app> \
  --resource-group <rg> \
  --settings "MY_SECRET=@Microsoft.KeyVault(SecretUri=https://<vault>.vault.azure.net/secrets/<name>/)"

# List current settings
az functionapp config appsettings list \
  --name <function-app> \
  --resource-group <rg> \
  --output table

# Scale out (Dedicated/Premium plans)
az functionapp scale config set \
  --name <function-app> \
  --resource-group <rg> \
  --minimum-instance-count 2 \
  --maximum-instance-count 20
```

---

## Anti-Patterns

- **Deploying directly to production without a staging slot** — use deployment slots for zero-downtime deploys.
- **Storing connection strings in app settings as plain text** — use Key Vault references.
- **Not setting `WEBSITE_RUN_FROM_PACKAGE=1`** on Consumption/Flex plans — running from a mounted zip package improves cold start time.
- **Committing `local.settings.json`** — contains secrets and local-only settings; always in `.gitignore`.
- **Using shared storage accounts for multiple production Function Apps** — use isolated storage per app to avoid storage throttling.
- **Not setting function timeout in `host.json`** — the default Consumption timeout is 5 minutes; set `functionTimeout` explicitly and alert when functions approach the limit.
