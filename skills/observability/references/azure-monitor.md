# Azure Monitor Reference

Azure-native observability: Log Analytics KQL, Application Insights, Azure Monitor alerts, and workbooks. Extend the `observability` skill with Azure-specific patterns when Azure Monitor or Application Insights SDK dependencies are detected.

---

## Detection Signals

Use when the project contains any of:
- `applicationinsights` package (`npm`, `pypi`, `Maven`, NuGet `Microsoft.ApplicationInsights.*`)
- `azure-monitor-opentelemetry` package (OTel + Azure Monitor exporter)
- `APPLICATIONINSIGHTS_CONNECTION_STRING` environment variable
- `Microsoft.Azure.Monitor` / `Azure.Monitor.OpenTelemetry.AspNetCore` NuGet packages
- Log Analytics workspace in Bicep/Terraform (`Microsoft.OperationalInsights/workspaces`)

---

## Architecture Overview

```
Applications / VMs / AKS
       |
       v
Application Insights SDK  ──────────────────┐
(or Azure Monitor OTel Exporter)            |
                                            v
                              Azure Monitor (data plane)
                                            |
                         ┌──────────────────┼──────────────────┐
                         v                  v                  v
               Log Analytics           Metrics Store      Distributed Trace
               (KQL query engine)      (time-series)         (Application Map)
                         |
                    ┌────┴─────┐
                    v          v
               Workbooks    Alerts
              (dashboards)  (action groups)
```

---

## Application Insights Setup

### Connection String (preferred over instrumentation key)

```bash
# Get the connection string
az monitor app-insights component show \
  --app <app-insights-name> \
  --resource-group <rg> \
  --query connectionString \
  --output tsv
```

Set as `APPLICATIONINSIGHTS_CONNECTION_STRING` in app settings — never hardcode.

### Node.js / TypeScript

```typescript
// applicationinsights@3.x (OTel-based)
import appInsights from "applicationinsights";

appInsights
  .setup()                    // reads APPLICATIONINSIGHTS_CONNECTION_STRING from env
  .setAutoCollectRequests(true)
  .setAutoCollectExceptions(true)
  .setAutoCollectDependencies(true)
  .setAutoCollectPerformance(true)
  .setSendLiveMetrics(true)
  .start();

// Manual telemetry
const client = appInsights.defaultClient;
client.trackEvent({ name: "UserSignup", properties: { userId: "123" } });
client.trackMetric({ name: "QueueDepth", value: 42 });
client.trackException({ exception: new Error("something failed") });
```

### Python

```python
# azure-monitor-opentelemetry (recommended for new projects)
from azure.monitor.opentelemetry import configure_azure_monitor

configure_azure_monitor(
    connection_string=os.environ["APPLICATIONINSIGHTS_CONNECTION_STRING"],
)

# OR: legacy applicationinsights package
from applicationinsights import TelemetryClient

client = TelemetryClient(os.environ["APPLICATIONINSIGHTS_CONNECTION_STRING"])
client.track_event("UserSignup", {"userId": "123"})
client.flush()
```

### Azure Functions (auto-instrumented)

Azure Functions auto-instruments Application Insights when `APPLICATIONINSIGHTS_CONNECTION_STRING` is set in app settings. No SDK code required — telemetry is collected automatically for HTTP triggers, dependencies, exceptions, and custom traces.

```bash
az functionapp config appsettings set \
  --name <function-app> \
  --resource-group <rg> \
  --settings "APPLICATIONINSIGHTS_CONNECTION_STRING=<connection-string>"
```

---

## KQL: Common Queries

### Request Rate and Error Rate (last 1 hour)

```kusto
requests
| where timestamp > ago(1h)
| summarize
    RequestRate = count() / 60.0,
    ErrorRate = countif(success == false) / 60.0,
    ErrorPct = 100.0 * countif(success == false) / count()
    by bin(timestamp, 1m)
| order by timestamp asc
```

### P50 / P95 / P99 Latency

```kusto
requests
| where timestamp > ago(1h) and success == true
| summarize
    P50 = percentile(duration, 50),
    P95 = percentile(duration, 95),
    P99 = percentile(duration, 99)
    by bin(timestamp, 5m), name
| order by timestamp asc
```

### Exceptions by Type

```kusto
exceptions
| where timestamp > ago(24h)
| summarize Count = count() by type, outerMessage
| order by Count desc
| take 20
```

### Dependency Failures (downstream service errors)

```kusto
dependencies
| where timestamp > ago(1h) and success == false
| summarize FailureCount = count() by target, name, resultCode
| order by FailureCount desc
```

### Trace Correlation (find logs for a specific request)

```kusto
// Find all telemetry for a specific operation
let operationId = "<operation-id>";
union requests, dependencies, exceptions, traces, customEvents
| where operation_Id == operationId
| project timestamp, itemType, name, message, duration, success, resultCode
| order by timestamp asc
```

### Availability (from availability tests)

```kusto
availabilityResults
| where timestamp > ago(24h)
| summarize
    Availability = 100.0 * countif(success == 1) / count(),
    FailureCount = countif(success == 0)
    by name, location
| order by Availability asc
```

---

## Azure Monitor Alerts

### Metric Alert (error rate threshold)

```bash
az monitor metrics alert create \
  --name "High Error Rate" \
  --resource-group <rg> \
  --scopes $(az monitor app-insights component show --app <ai-name> -g <rg> --query id -o tsv) \
  --condition "avg requests/failed > 5 where name includes 'GET'" \
  --window-size 5m \
  --evaluation-frequency 1m \
  --severity 2 \
  --action $(az monitor action-group show --name <action-group> -g <rg> --query id -o tsv)
```

### Log Alert (KQL-based)

```bash
az monitor scheduled-query create \
  --name "Spike in Exceptions" \
  --resource-group <rg> \
  --scopes $(az monitor log-analytics workspace show --workspace-name <workspace> -g <rg> --query id -o tsv) \
  --condition-query "exceptions | where timestamp > ago(5m) | count" \
  --condition-threshold 10 \
  --condition-operator "GreaterThan" \
  --evaluation-frequency "5m" \
  --window-duration "5m" \
  --severity 2 \
  --action-groups $(az monitor action-group show --name <action-group> -g <rg> --query id -o tsv)
```

### Action Groups

```bash
# Create action group for email + webhook
az monitor action-group create \
  --name <group-name> \
  --resource-group <rg> \
  --short-name <short-name> \
  --email-receiver name=oncall address=oncall@example.com \
  --webhook-receiver name=pagerduty \
    service-uri="https://events.pagerduty.com/integration/<key>/enqueue"
```

---

## Burn-Rate Alerting (SLO)

Azure Monitor does not have native multi-window burn-rate support. Approximate with two log alerts:

```kusto
-- Fast-burn alert (1h window, 14.4x burn rate for 1% error budget in 30 days)
-- Fires when: error rate over 1h > 14.4% (14.4x normal for 99.9% SLO)
requests
| where timestamp > ago(1h)
| summarize ErrorRate = 100.0 * countif(success == false) / count()
| where ErrorRate > 14.4

-- Slow-burn alert (6h window, 6x burn rate)
requests
| where timestamp > ago(6h)
| summarize ErrorRate = 100.0 * countif(success == false) / count()
| where ErrorRate > 6.0
```

---

## Workbooks

Use workbooks for pre-built dashboards:

1. Azure Portal → Application Insights → Workbooks
2. Built-in templates: **Application Health**, **Performance**, **Failures**, **Usage**
3. Export workbook JSON for IaC-managed deployment via ARM/Bicep

```bicep
resource workbook 'Microsoft.Insights/workbooks@2022-04-01' = {
  name: guid(resourceGroup().id, 'my-workbook')
  location: location
  kind: 'shared'
  properties: {
    displayName: 'Service Health'
    serializedData: loadTextContent('workbooks/service-health.json')
    sourceId: appInsights.id
    category: 'workbook'
  }
}
```

---

## Sampling

Application Insights samples telemetry by default (adaptive sampling) to control ingestion cost. For high-volume services:

```typescript
// Fixed-rate sampling — keep 10% of telemetry
appInsights.setup().setAutoCollectDependencies(true);
appInsights.defaultClient.config.samplingPercentage = 10;
```

Always keep exceptions at 100% sampling regardless of other sampling settings — exceptions are critical signals with low volume.

```typescript
appInsights.defaultClient.addTelemetryProcessor((envelope) => {
  if (envelope.data.baseType === "ExceptionData") {
    envelope.sampleRate = 100;  // Always keep exceptions
  }
  return true;
});
```
