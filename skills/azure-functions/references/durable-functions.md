# Durable Functions

Durable Functions extends Azure Functions with stateful orchestrations — long-running workflows, fan-out/fan-in, human approval gates, and eternal loops — without managing state infrastructure yourself. State is stored in Azure Storage (history table + queue).

---

## Core Concepts

| Concept | Description |
|---------|-------------|
| **Orchestrator function** | Coordinates activities; replays from event history on restart; must be deterministic |
| **Activity function** | Does the actual work (I/O, API calls); can be non-deterministic |
| **Entity function** | Stateful actors with durable state; event-sourced object model |
| **Client function** | Starts orchestrations, queries status, sends events; triggered by HTTP/queue/timer |

**Determinism rule for orchestrators:** Never use `Date.now()`, `Math.random()`, or async I/O directly in orchestrator code. Use `context.df.currentUtcDateTime` and delegate I/O to activities.

---

## Pattern 1: Sequential Workflow

```typescript
// orchestrator — TypeScript
import * as df from "durable-functions";

df.app.orchestration("sequentialWorkflow", function* (context: df.OrchestrationContext) {
  const result1 = yield context.df.callActivity("StepOne", context.df.getInput<string>());
  const result2 = yield context.df.callActivity("StepTwo", result1);
  const result3 = yield context.df.callActivity("StepThree", result2);
  return result3;
});

df.app.activity("StepOne", { handler: async (input: string) => `step-one:${input}` });
df.app.activity("StepTwo", { handler: async (input: string) => `step-two:${input}` });
df.app.activity("StepThree", { handler: async (input: string) => `step-three:${input}` });
```

---

## Pattern 2: Fan-Out / Fan-In

```typescript
// orchestrator — TypeScript
df.app.orchestration("fanOutFanIn", function* (context: df.OrchestrationContext) {
  const items = context.df.getInput<string[]>();

  // Fan-out: launch all tasks in parallel
  const tasks = items.map(item => context.df.callActivity("ProcessItem", item));

  // Fan-in: wait for all to complete
  const results = yield context.df.Task.all(tasks);

  return results;
});

df.app.activity("ProcessItem", {
  handler: async (item: string) => {
    // I/O, API calls, transformations
    return { item, processed: true };
  },
});
```

**`Task.any` vs `Task.all`:**
- `Task.all(tasks)` — wait for all tasks to finish (fan-in)
- `Task.any(tasks)` — proceed when the first task finishes (race pattern)

---

## Pattern 3: Human Approval (External Event)

```typescript
// orchestrator — TypeScript
df.app.orchestration("humanApproval", function* (context: df.OrchestrationContext) {
  const request = context.df.getInput<{ id: string; details: string }>();

  // Send approval request (via activity — email, Slack, Teams Adaptive Card)
  yield context.df.callActivity("SendApprovalRequest", {
    instanceId: context.df.instanceId,
    ...request,
  });

  // Wait for external event (approval or rejection) with timeout
  const approvalTask = context.df.waitForExternalEvent<{ approved: boolean }>("ApprovalResponse");
  const timeoutTask = context.df.createTimer(
    new Date(context.df.currentUtcDateTime.getTime() + 24 * 60 * 60 * 1000)  // 24h timeout
  );

  const winner = yield context.df.Task.any([approvalTask, timeoutTask]);

  if (winner === timeoutTask) {
    // Escalate or auto-reject on timeout
    yield context.df.callActivity("HandleTimeout", request.id);
    return { approved: false, reason: "timeout" };
  }

  timeoutTask.cancel();
  const response = approvalTask.result;

  if (response.approved) {
    yield context.df.callActivity("ExecuteApprovedAction", request);
  } else {
    yield context.df.callActivity("HandleRejection", request.id);
  }

  return response;
});
```

**Sending the external event (from an HTTP trigger):**

```typescript
import { app, HttpRequest, HttpResponseInit, InvocationContext } from "@azure/functions";
import * as df from "durable-functions";

app.http("approvalCallback", {
  methods: ["POST"],
  authLevel: "function",
  handler: async (request: HttpRequest, context: InvocationContext): Promise<HttpResponseInit> => {
    const client = df.getClient(context);
    const instanceId = request.query.get("instanceId")!;
    const body = await request.json() as { approved: boolean };

    await client.raiseEvent(instanceId, "ApprovalResponse", body);
    return { status: 200, body: "Event sent" };
  },
  extraInputs: [df.input.durableClient()],
});
```

---

## Pattern 4: Eternal Orchestration (Polling Loop)

```typescript
// orchestrator — TypeScript
df.app.orchestration("pollingLoop", function* (context: df.OrchestrationContext) {
  const config = context.df.getInput<{ resourceId: string; checkIntervalMinutes: number }>();

  // Check status
  const status = yield context.df.callActivity("CheckResourceStatus", config.resourceId);

  if (status === "complete") {
    yield context.df.callActivity("HandleCompletion", config.resourceId);
    return; // Orchestration ends
  }

  // Wait before next check
  const nextCheckTime = new Date(
    context.df.currentUtcDateTime.getTime() + config.checkIntervalMinutes * 60 * 1000
  );
  yield context.df.createTimer(nextCheckTime);

  // Continue as new — replaces history, prevents unbounded growth
  context.df.continueAsNew(config);
});
```

**`continueAsNew`** is essential for eternal orchestrations — it replaces the orchestration history with a fresh start, preventing the event history from growing unboundedly.

---

## Client: Starting and Managing Orchestrations

```typescript
// HTTP trigger that starts an orchestration
app.http("startOrchestration", {
  methods: ["POST"],
  authLevel: "function",
  extraInputs: [df.input.durableClient()],
  handler: async (request: HttpRequest, context: InvocationContext): Promise<HttpResponseInit> => {
    const client = df.getClient(context);
    const input = await request.json();

    const instanceId = await client.startNew("myOrchestration", { input });

    // Returns management URLs (status, terminate, raise event)
    return client.createCheckStatusResponse(request, instanceId);
  },
});
```

**Management operations:**

```typescript
// Query status
const status = await client.getStatus(instanceId);
// status.runtimeStatus: "Running" | "Completed" | "Failed" | "Terminated" | "Pending"

// Terminate
await client.terminate(instanceId, "User requested cancellation");

// Purge history (completed orchestrations)
await client.purgeInstanceHistory(instanceId);
```

---

## Storage Backend Options

| Backend | Default | When to Change |
|---------|---------|---------------|
| Azure Storage (tables + queues) | Yes | Default for most workloads |
| Microsoft SQL Server (MSSQL) | No | On-premises or regulated environments |
| Azure SQL | No | SQL-preferred shops, existing SQL estate |
| Netherite (Event Hubs + Azure Storage) | No | High-throughput, low-latency requirements |

Configure in `host.json`:

```json
{
  "version": "2.0",
  "extensions": {
    "durableTask": {
      "storageProvider": {
        "type": "azure_storage",
        "connectionStringName": "AzureWebJobsStorage",
        "partitionCount": 4
      }
    }
  }
}
```

---

## Anti-Patterns

- **I/O or non-deterministic code in orchestrators** — always delegate to activities. The orchestrator replays; non-determinism causes divergence.
- **Unbounded fan-out without batching** — `Task.all` on thousands of items creates thousands of activity tasks simultaneously; batch them.
- **Forgetting to cancel timers** — in `Task.any`, always cancel the timer task that didn't win to avoid ghost timers.
- **Not using `continueAsNew` in eternal orchestrations** — history grows unboundedly; replay time increases linearly.
- **Storing large objects in orchestration input/output** — Durable Functions serializes state to Storage tables; large payloads cause performance degradation. Reference data by ID; load in activities.
