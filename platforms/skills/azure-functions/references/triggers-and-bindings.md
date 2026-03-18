# Azure Functions: Triggers and Bindings

Code examples for common trigger and binding patterns across supported languages.

---

## HTTP Trigger

### TypeScript (Node.js v4 programming model)

```typescript
import { app, HttpRequest, HttpResponseInit, InvocationContext } from "@azure/functions";

app.http("myHttpFunction", {
  methods: ["GET", "POST"],
  authLevel: "anonymous",
  handler: async (request: HttpRequest, context: InvocationContext): Promise<HttpResponseInit> => {
    context.log("HTTP trigger fired:", request.method, request.url);
    const name = request.query.get("name") ?? "World";
    return { body: `Hello, ${name}!` };
  },
});
```

### Python (v2 programming model)

```python
import azure.functions as func
import logging

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

@app.route(route="myHttpFunction", methods=["GET", "POST"])
def my_http_function(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("HTTP trigger fired")
    name = req.params.get("name") or "World"
    return func.HttpResponse(f"Hello, {name}!")
```

### Go (custom handler — HTTP passthrough)

```go
// Custom handler: Functions host forwards HTTP to your Go server on localhost:PORT
package main

import (
    "encoding/json"
    "net/http"
    "os"
)

func main() {
    port := os.Getenv("FUNCTIONS_CUSTOMHANDLER_PORT")
    if port == "" {
        port = "8080"
    }
    http.HandleFunc("/api/myHttpFunction", func(w http.ResponseWriter, r *http.Request) {
        name := r.URL.Query().Get("name")
        if name == "" {
            name = "World"
        }
        json.NewEncoder(w).Encode(map[string]string{"message": "Hello, " + name + "!"})
    })
    http.ListenAndServe(":"+port, nil)
}
```

**`host.json` for custom handler:**
```json
{
  "version": "2.0",
  "customHandler": {
    "description": {
      "defaultExecutablePath": "handler",
      "workingDirectory": "",
      "arguments": []
    },
    "enableForwardingHttpRequest": true
  }
}
```

---

## Timer Trigger

### TypeScript

```typescript
import { app, InvocationContext, Timer } from "@azure/functions";

app.timer("myTimerFunction", {
  schedule: "0 */5 * * * *",  // Every 5 minutes (6-part CRON)
  handler: async (timer: Timer, context: InvocationContext): Promise<void> => {
    context.log("Timer fired at:", new Date().toISOString());
    if (timer.isPastDue) {
      context.log("Timer was past due — running catch-up");
    }
  },
});
```

**CRON format:** `{second} {minute} {hour} {day} {month} {day-of-week}`
- `0 0 */6 * * *` — Every 6 hours
- `0 0 9 * * 1-5` — Weekdays at 9:00 AM
- `0 30 8 * * *` — Daily at 8:30 AM

### Python

```python
@app.timer_trigger(schedule="0 */5 * * * *", arg_name="timer", run_on_startup=False)
def my_timer_function(timer: func.TimerRequest) -> None:
    logging.info("Timer fired at: %s", datetime.utcnow().isoformat())
    if timer.past_due:
        logging.info("Timer was past due")
```

---

## Service Bus Trigger

### TypeScript — Queue (with dead-letter handling)

```typescript
import { app, InvocationContext, ServiceBusReceivedMessage } from "@azure/functions";

app.serviceBusTrigger("myServiceBusFunction", {
  queueName: "my-queue",
  connection: "MyServiceBusConnection",  // App setting name
  handler: async (message: ServiceBusReceivedMessage, context: InvocationContext): Promise<void> => {
    context.log("Message body:", message.body);
    context.log("Delivery count:", message.deliveryCount);

    // If processing fails, throw an error — Functions will retry up to maxDeliveryCount
    // After maxDeliveryCount failures, message goes to dead-letter queue automatically
  },
});
```

### Python — Topic Subscription

```python
@app.service_bus_topic_trigger(
    arg_name="msg",
    topic_name="my-topic",
    subscription_name="my-subscription",
    connection="MyServiceBusConnection",
)
def my_servicebus_function(msg: func.ServiceBusMessage) -> None:
    body = msg.get_body().decode("utf-8")
    logging.info("Received message: %s", body)
    logging.info("Delivery count: %d", msg.delivery_count)
    logging.info("Message ID: %s", msg.message_id)
```

---

## Blob Trigger

### TypeScript — React to new blobs

```typescript
import { app, InvocationContext, StorageBlob } from "@azure/functions";

app.storageBlob("myBlobFunction", {
  path: "uploads/{name}",       // {name} captures the blob name
  connection: "AzureWebJobsStorage",
  handler: async (blob: StorageBlob, context: InvocationContext): Promise<void> => {
    context.log("Blob trigger fired for:", context.triggerMetadata?.name);
    context.log("Blob size:", blob.length, "bytes");
  },
});
```

**Note:** Blob trigger uses polling (default 5 seconds) or Event Grid (recommended for latency < 1 second). Use Event Grid subscription → Function trigger for near-real-time blob processing.

---

## Event Grid Trigger

### TypeScript — CloudEvents schema

```typescript
import { app, InvocationContext } from "@azure/functions";

app.eventGrid("myEventGridFunction", {
  handler: async (event: unknown, context: InvocationContext): Promise<void> => {
    context.log("Event received:", JSON.stringify(event));
    const gridEvent = event as {
      id: string;
      eventType: string;
      subject: string;
      data: unknown;
    };
    context.log("Event type:", gridEvent.eventType);
  },
});
```

---

## Output Bindings

### Write to Service Bus + Cosmos DB from HTTP trigger (TypeScript)

```typescript
import { app, HttpRequest, HttpResponseInit, InvocationContext, output } from "@azure/functions";

const serviceBusOutput = output.serviceBus({
  queueName: "results-queue",
  connection: "MyServiceBusConnection",
});

const cosmosOutput = output.cosmosDB({
  databaseName: "mydb",
  containerName: "results",
  createIfNotExists: true,
  connection: "MyCosmosConnection",
});

app.http("processRequest", {
  methods: ["POST"],
  authLevel: "function",
  extraOutputs: [serviceBusOutput, cosmosOutput],
  handler: async (request: HttpRequest, context: InvocationContext): Promise<HttpResponseInit> => {
    const body = await request.json() as { id: string; data: unknown };

    // Write to Service Bus
    context.extraOutputs.set(serviceBusOutput, { id: body.id, processed: true });

    // Write to Cosmos DB
    context.extraOutputs.set(cosmosOutput, { id: body.id, result: body.data, timestamp: new Date().toISOString() });

    return { status: 202, body: "Accepted" };
  },
});
```

---

## Auth Levels

| Level | Description | Use When |
|-------|-------------|----------|
| `anonymous` | No auth required | Public APIs, health checks, webhooks with own signature validation |
| `function` | Function key required | Internal APIs, trusted service-to-service (pass key in `x-functions-key` header or `code` query param) |
| `admin` | Host-level key required | Admin operations only |

For production, prefer Entra ID authentication over function keys — use Easy Auth or validate bearer tokens in the handler.
