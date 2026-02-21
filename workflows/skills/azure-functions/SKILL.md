---
name: azure-functions
description: "Azure Functions development guidance: trigger and binding patterns, Durable Functions orchestrations, local development with func CLI and Azurite, deployment to Consumption/Premium/Dedicated plans, deployment slots, and the Azure Functions MCP extension for exposing functions as AI tools."
user-invocable: true
argument-hint: "[triggers|durable|local|deploy|mcp]"
model: sonnet
---

# Azure Functions

Development guidance for Azure Functions: triggers, bindings, Durable Functions, local dev, deployment, and MCP integration.

---

## When to Use

- Implementing event-driven workloads (HTTP, queue, timer, blob, Service Bus, Event Grid triggers)
- Building Durable Functions orchestrations (fan-out/fan-in, eternal orchestrations, human approval)
- Setting up local development with `func` CLI and Azurite
- Choosing a hosting plan (Consumption vs Premium vs Dedicated)
- Deploying Functions via `az`, `azd`, or CI/CD pipelines
- Exposing Azure Functions as MCP tools for AI agents

---

## Quick Start

```
/azure-functions triggers    # Trigger types, binding input/output patterns
/azure-functions durable     # Durable Functions: orchestrators, activities, patterns
/azure-functions local       # Local dev: func CLI, Azurite, local.settings.json
/azure-functions deploy      # Hosting plan selection, deployment, slots
/azure-functions mcp         # MCP extension: expose functions as AI tools
```

---

## Trigger and Binding Overview

| Trigger | Language Support | When to Use |
|---------|-----------------|-------------|
| HTTP | All | REST APIs, webhooks, MCP tools |
| Timer (CRON) | All | Scheduled jobs, cleanup, polling |
| Azure Blob | All | React to blob creates/updates |
| Azure Service Bus | All | Reliable message processing |
| Azure Service Bus (sessions) | All | Ordered, per-session processing |
| Azure Event Grid | All | CloudEvents-based event routing |
| Azure Event Hubs | All | High-throughput telemetry ingestion |
| Azure Queue Storage | All | Simple FIFO queuing |
| Cosmos DB | All | React to document changes (change feed) |
| Durable (orchestration client) | All | Start orchestrations from external triggers |

### Output Bindings (declarative, no SDK required)

```
Input trigger → Function logic → Output bindings
```

Output bindings: Service Bus message, Blob, Cosmos DB document, SignalR, Event Hubs, Queue Storage, Durable activity scheduling.

---

## Local Development

**Prerequisites:**
- Azure Functions Core Tools: `npm install -g azure-functions-core-tools@4 --unsafe-perm true`
- Azurite (local Storage emulator): `npm install -g azurite`
- Language runtime for your target (Node.js, Python, Go, .NET)

```bash
# Initialize a new Functions project
func init MyFunctionApp --worker-runtime node     # or python, dotnet, custom
cd MyFunctionApp

# Create a function
func new --name HttpTrigger --template "HTTP trigger"
func new --name TimerTrigger --template "Timer trigger"
func new --name ServiceBusTrigger --template "Azure Service Bus trigger"

# Start Azurite (Storage emulator) in a separate terminal
azurite --location ~/.azurite --debug ~/.azurite/debug.log

# Start the Functions host
func start

# Run a specific function
func run HttpTrigger
```

### `local.settings.json`

```json
{
  "IsEncrypted": false,
  "Values": {
    "AzureWebJobsStorage": "UseDevelopmentStorage=true",
    "FUNCTIONS_WORKER_RUNTIME": "node",
    "MyServiceBusConnection": "Endpoint=sb://...",
    "MyCosmosConnection": "AccountEndpoint=https://..."
  }
}
```

**Never commit `local.settings.json`** — add to `.gitignore`. Use Key Vault references or environment-specific config for production values.

See `references/local-development.md` for debugging, remote attach, and Azurite configuration.

---

## Hosting Plan Selection

| Plan | Cold Start | Scale | Max Duration | Best For |
|------|-----------|-------|-------------|----------|
| **Consumption** | Yes (seconds) | Auto (0→∞) | 10 min | Infrequent, burst, cost-sensitive |
| **Flex Consumption** | Minimal | Auto (configurable min) | 60 min | Most production workloads (2024+) |
| **Premium** | No (pre-warmed) | Auto | 60 min | Latency-sensitive, VNet integration |
| **Dedicated (App Service)** | No | Manual or ASP autoscale | Unlimited | Always-on, existing App Service Plan |
| **Container Apps** | No | Auto | Unlimited | Custom runtimes, sidecar patterns |

**2025 Recommendation:** Flex Consumption is the preferred plan for new production deployments — it combines Consumption pricing with configurable minimum instances (eliminating cold starts when needed) and 60-minute max duration.

---

## Deployment

```bash
# Deploy via Azure CLI
az functionapp deployment source config-zip \
  --resource-group <rg> \
  --name <function-app> \
  --src build.zip

# Deploy via func CLI
func azure functionapp publish <function-app>

# Deploy via azd
azd deploy

# List deployed functions
az functionapp function list --name <function-app> --resource-group <rg> --output table
```

### Deployment Slots

Deployment slots enable zero-downtime releases with instant swap rollback.

```bash
# Create a staging slot
az functionapp deployment slot create \
  --name <function-app> \
  --resource-group <rg> \
  --slot staging

# Deploy to staging
az functionapp deployment source config-zip \
  --resource-group <rg> \
  --name <function-app> \
  --slot staging \
  --src build.zip

# Swap staging → production (atomic)
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

See `references/deployment-patterns.md` for CI/CD pipeline integration, slot-specific settings, and traffic splitting.

---

## Azure Functions MCP Extension

The Azure Functions MCP extension (GA) allows HTTP-triggered functions to be exposed as MCP tools — enabling AI agents to invoke functions directly.

```json
// host.json — enable MCP extension
{
  "version": "2.0",
  "extensionBundle": {
    "id": "Microsoft.Azure.Functions.ExtensionBundle",
    "version": "[4.0.0, 5.0.0)"
  },
  "extensions": {
    "mcp": {
      "instructions": "You are a helpful assistant. Use these tools to complete tasks."
    }
  }
}
```

```typescript
// TypeScript — HTTP function exposed as MCP tool
import { app, HttpRequest, HttpResponseInit, InvocationContext } from "@azure/functions";

app.http("listOrders", {
  methods: ["GET"],
  authLevel: "function",
  handler: async (request: HttpRequest, context: InvocationContext): Promise<HttpResponseInit> => {
    const customerId = request.query.get("customerId");
    // ... business logic
    return { jsonBody: orders };
  },
  // MCP tool metadata
  extraInputs: [],
  extraOutputs: [],
});
```

**Auth:** The MCP extension uses On-Behalf-Of (OBO) auth — the calling user's token is forwarded. Requires Entra ID app registration with appropriate API permissions.

**Transport:** Streamable HTTP (SSE). Compatible with Claude, Claude Desktop, and Cursor.

See `references/triggers-and-bindings.md` for binding code examples per language.

---

## Cold Start Mitigation

- **Flex Consumption:** Set `minimumInstanceCount > 0` to keep warm instances.
- **Premium:** Always-ready instances; no cold start.
- **Consumption with `WEBSITE_RUN_FROM_PACKAGE=1`:** Reduces startup time by running from a mounted zip.
- **Keep function packages small:** Remove unused dependencies; tree-shake Node.js bundles.
- **Avoid heavy initialization at module level:** Move SDK client creation to lazy initialization inside the handler or use module-level singletons carefully.

---

## Key References

| Reference | Contents |
|-----------|----------|
| `references/triggers-and-bindings.md` | HTTP, Timer, Service Bus, Event Grid, Blob trigger code examples |
| `references/durable-functions.md` | Orchestrators, activities, fan-out/fan-in, eternal orchestrations, human approval |
| `references/local-development.md` | func CLI, Azurite, debugging, remote attach, test invocation |
| `references/deployment-patterns.md` | Plan comparison, CI/CD pipelines, deployment slots, azd integration |
