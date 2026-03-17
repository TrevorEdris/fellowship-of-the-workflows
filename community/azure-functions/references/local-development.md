# Azure Functions Local Development

---

## Prerequisites

```bash
# Azure Functions Core Tools (v4 — supports Node.js, Python, .NET, PowerShell, custom)
npm install -g azure-functions-core-tools@4 --unsafe-perm true

# Verify installation
func --version   # Should be 4.x

# Azurite — local Azure Storage emulator (replaces legacy Azure Storage Emulator)
npm install -g azurite

# Docker (optional — for Azurite in container or for testing containerized functions)
# https://docs.docker.com/get-docker/
```

---

## Project Structure

```
MyFunctionApp/
├── host.json                  # Runtime configuration
├── local.settings.json        # Local environment settings (not committed)
├── package.json               # Node.js project descriptor
├── tsconfig.json              # TypeScript config
├── src/
│   └── functions/
│       ├── httpTrigger.ts
│       ├── timerTrigger.ts
│       └── serviceBusTrigger.ts
└── .funcignore                # Files to exclude from deployment
```

### `host.json`

```json
{
  "version": "2.0",
  "logging": {
    "applicationInsights": {
      "samplingSettings": {
        "isEnabled": true,
        "excludedTypes": "Request"
      }
    }
  },
  "functionTimeout": "00:10:00",
  "extensions": {
    "serviceBus": {
      "prefetchCount": 20,
      "maxAutoLockRenewalDuration": "00:05:00"
    }
  }
}
```

### `local.settings.json`

```json
{
  "IsEncrypted": false,
  "Values": {
    "AzureWebJobsStorage": "UseDevelopmentStorage=true",
    "FUNCTIONS_WORKER_RUNTIME": "node",
    "MyServiceBusConnection": "Endpoint=sb://<namespace>.servicebus.windows.net/;SharedAccessKeyName=...",
    "MyCosmosConnection": "AccountEndpoint=https://<account>.documents.azure.com:443/;AccountKey=...",
    "AZURE_CLIENT_ID": "",
    "AZURE_TENANT_ID": "",
    "AZURE_SUBSCRIPTION_ID": ""
  },
  "Host": {
    "LocalHttpPort": 7071,
    "CORS": "*"
  }
}
```

**Never commit `local.settings.json`.** Add to `.gitignore`.

---

## Starting Azurite

Azurite emulates Azure Blob, Queue, and Table Storage locally.

```bash
# Start all services (Blob :10000, Queue :10001, Table :10002)
azurite --location ~/.azurite --debug ~/.azurite/debug.log

# Start specific services
azurite-blob --location ~/.azurite
azurite-queue --location ~/.azurite

# Or via Docker
docker run -p 10000:10000 -p 10001:10001 -p 10002:10002 \
  mcr.microsoft.com/azure-storage/azurite

# VS Code extension: "Azurite" (ms-azuretools.vscode-azurite)
# Start/stop from VS Code status bar
```

Connection string for Azurite:
```
UseDevelopmentStorage=true
# or explicit:
DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;AccountKey=<key>;BlobEndpoint=http://127.0.0.1:10000/devstoreaccount1;...
```

---

## Running Functions Locally

```bash
# Start the Functions host
func start

# Start with verbose logging
func start --verbose

# Start on a different port
func start --port 7072

# Run a specific function by name (non-HTTP triggers)
func run HttpTrigger --content '{"name":"world"}'

# Watch mode (recompile on file changes — TypeScript)
npm run build:watch &  # Start TypeScript compiler in watch mode
func start             # Then start Functions host
```

---

## Invoking Functions Locally

### HTTP Trigger

```bash
# GET
curl http://localhost:7071/api/myHttpFunction?name=world

# POST with JSON body
curl -X POST http://localhost:7071/api/myHttpFunction \
  -H "Content-Type: application/json" \
  -d '{"key": "value"}'

# With function key
curl "http://localhost:7071/api/myHttpFunction?code=<function-key>"
```

### Non-HTTP Triggers (simulated via admin API)

```bash
# Manually trigger a timer or queue trigger
curl -X POST http://localhost:7071/admin/functions/myTimerFunction \
  -H "Content-Type: application/json" \
  -d '{}'
```

---

## Debugging

### VS Code (recommended)

`.vscode/launch.json`:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Attach to Node Functions",
      "type": "node",
      "request": "attach",
      "port": 9229,
      "preLaunchTask": "func: host start"
    }
  ]
}
```

`.vscode/tasks.json`:

```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "type": "func",
      "label": "func: host start",
      "command": "host start",
      "problem_matcher": "$func-node-watch",
      "isBackground": true,
      "dependsOn": "npm build (functions)"
    }
  ]
}
```

Start debugging: `F5` → Functions host starts → attach debugger → set breakpoints in function handlers.

### Remote Debug (App Service / Container Apps)

```bash
# Enable remote debugging on App Service (not recommended for production)
az webapp config set \
  --name <app> \
  --resource-group <rg> \
  --remote-debugging-enabled true \
  --remote-debugging-version VS2022
```

---

## Connecting to Real Azure Services Locally

For triggers that require real Azure services (Service Bus, Event Grid subscriptions), you cannot use Azurite. Options:

1. **Use a dev Azure subscription** — connect `local.settings.json` to real service connection strings. Keep the dev environment isolated from staging/production.
2. **Managed Identity locally via `az login`** — `DefaultAzureCredential` falls through to `AzureCliCredential` when running locally. Ensure your user has the required RBAC roles on the dev resources.
3. **Service Bus tunneling** — use `ngrok` or Azure Dev Tunnels to expose a local HTTP endpoint for Event Grid push subscriptions.

---

## Common Issues

| Issue | Cause | Fix |
|-------|-------|-----|
| `Port 7071 is in use` | Another process is using the port | `func start --port 7072` or kill the existing process |
| `Storage emulator is not running` | Azurite not started | Start Azurite before `func start` |
| `Cannot find module '@azure/functions'` | Missing npm dependencies | `npm install` |
| Timer trigger not firing locally | `runOnStartup` not set | Add `runOnStartup: true` to timer trigger options for local testing |
| `AZURE_WEBJOBS_STORAGE is missing` | `local.settings.json` missing or incorrect | Set `AzureWebJobsStorage` to `UseDevelopmentStorage=true` |
| Service Bus trigger not firing | Invalid connection string or queue doesn't exist | Verify connection string and queue name in Service Bus Explorer |
