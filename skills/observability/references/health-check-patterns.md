# Health Check Patterns Reference

## Endpoint Semantics

| Endpoint | Kubernetes Probe | Purpose | Fail Action |
|----------|-----------------|---------|-------------|
| `/livez` | Liveness probe | Is the process alive and not deadlocked? | Restart the container |
| `/readyz` | Readiness probe | Is the service ready to serve traffic? | Remove from load balancer |
| `/healthz` | Either (deprecated) | Legacy composite check | Varies |
| `/metrics` | Not a probe | Prometheus metrics scrape | N/A |

**Critical distinction:**
- **Liveness** should be extremely lightweight — only detect fatal states (deadlock, OOM, unrecoverable panic). Do NOT check database connectivity in a liveness probe. A database outage should remove the pod from rotation, not restart it.
- **Readiness** checks external dependencies. If the database is unreachable, the pod should return 503 on `/readyz` to be removed from the load balancer, but remain alive.

---

## Response Schema

**Success (HTTP 200):**
```json
{
  "status": "ok"
}
```

**Degraded readiness (HTTP 503):**
```json
{
  "status": "degraded",
  "checks": {
    "database": "ok",
    "cache": "failed: connection refused after 3 retries",
    "message_queue": "ok"
  }
}
```

**Liveness failure (HTTP 503):**
```json
{
  "status": "failed",
  "reason": "goroutine leak: 10000 active goroutines (threshold: 1000)"
}
```

---

## Implementation Examples

### Go (Gin)

```go
// Liveness — process alive check only
router.GET("/livez", func(c *gin.Context) {
    c.JSON(http.StatusOK, gin.H{"status": "ok"})
})

// Readiness — check all critical dependencies
router.GET("/readyz", func(c *gin.Context) {
    checks := map[string]string{}
    httpStatus := http.StatusOK
    overallStatus := "ok"

    // Database check
    ctx, cancel := context.WithTimeout(c.Request.Context(), 2*time.Second)
    defer cancel()
    if err := db.PingContext(ctx); err != nil {
        checks["database"] = fmt.Sprintf("failed: %v", err)
        httpStatus = http.StatusServiceUnavailable
        overallStatus = "degraded"
    } else {
        checks["database"] = "ok"
    }

    // Redis check (if applicable)
    if rdb != nil {
        if err := rdb.Ping(ctx).Err(); err != nil {
            checks["cache"] = fmt.Sprintf("failed: %v", err)
            httpStatus = http.StatusServiceUnavailable
            overallStatus = "degraded"
        } else {
            checks["cache"] = "ok"
        }
    }

    c.JSON(httpStatus, gin.H{
        "status": overallStatus,
        "checks": checks,
    })
})
```

### Node.js (Express)

```javascript
// Liveness
app.get('/livez', (req, res) => {
  res.status(200).json({ status: 'ok' });
});

// Readiness
app.get('/readyz', async (req, res) => {
  const checks = {};
  let degraded = false;

  // Database check
  try {
    await db.query('SELECT 1');
    checks.database = 'ok';
  } catch (err) {
    checks.database = `failed: ${err.message}`;
    degraded = true;
  }

  // Redis check
  try {
    await redisClient.ping();
    checks.cache = 'ok';
  } catch (err) {
    checks.cache = `failed: ${err.message}`;
    degraded = true;
  }

  const status = degraded ? 503 : 200;
  res.status(status).json({
    status: degraded ? 'degraded' : 'ok',
    checks,
  });
});
```

### Python (FastAPI)

```python
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import asyncio

app = FastAPI()

@app.get("/livez")
async def livez():
    return {"status": "ok"}

@app.get("/readyz")
async def readyz(db: AsyncSession = Depends(get_async_db)):
    checks = {}
    degraded = False

    # Database check with timeout
    try:
        async with asyncio.timeout(2.0):
            await db.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as e:
        checks["database"] = f"failed: {str(e)}"
        degraded = True

    # Cache check
    try:
        async with asyncio.timeout(1.0):
            await redis_client.ping()
        checks["cache"] = "ok"
    except Exception as e:
        checks["cache"] = f"failed: {str(e)}"
        degraded = True

    status_code = 503 if degraded else 200
    return JSONResponse(
        status_code=status_code,
        content={
            "status": "degraded" if degraded else "ok",
            "checks": checks,
        }
    )
```

### Rust (Axum)

```rust
use axum::{
    extract::State,
    http::StatusCode,
    response::Json,
    routing::get,
    Router,
};
use serde_json::{json, Value};
use std::collections::HashMap;

async fn livez() -> (StatusCode, Json<Value>) {
    (StatusCode::OK, Json(json!({"status": "ok"})))
}

async fn readyz(State(state): State<AppState>) -> (StatusCode, Json<Value>) {
    let mut checks = HashMap::new();
    let mut degraded = false;

    // Database ping with timeout
    match tokio::time::timeout(
        std::time::Duration::from_secs(2),
        state.db.ping(),
    ).await {
        Ok(Ok(_)) => { checks.insert("database", "ok"); }
        Ok(Err(e)) => {
            checks.insert("database", "failed");
            degraded = true;
            tracing::error!(error = %e, "database health check failed");
        }
        Err(_) => {
            checks.insert("database", "timeout");
            degraded = true;
        }
    }

    let status = if degraded { StatusCode::SERVICE_UNAVAILABLE } else { StatusCode::OK };
    let body = json!({
        "status": if degraded { "degraded" } else { "ok" },
        "checks": checks,
    });
    (status, Json(body))
}

// Register routes — BEFORE tracing middleware to exclude from traces
let app = Router::new()
    .route("/livez", get(livez))
    .route("/readyz", get(readyz))
    .layer(OtelAxumLayer::default())  // health routes registered before OTel layer
    .with_state(state);
```

---

## Kubernetes Probe Configuration

```yaml
apiVersion: apps/v1
kind: Deployment
spec:
  template:
    spec:
      containers:
        - name: order-service
          ports:
            - containerPort: 8080

          livenessProbe:
            httpGet:
              path: /livez
              port: 8080
            initialDelaySeconds: 15    # Give the service time to start
            periodSeconds: 10          # Check every 10 seconds
            timeoutSeconds: 5          # Fail if no response in 5s
            failureThreshold: 3        # Restart after 3 consecutive failures
            successThreshold: 1

          readinessProbe:
            httpGet:
              path: /readyz
              port: 8080
            initialDelaySeconds: 5     # Shorter delay — can check sooner
            periodSeconds: 5           # Check every 5 seconds
            timeoutSeconds: 3          # Shorter timeout — fail fast
            failureThreshold: 3        # Remove from LB after 3 failures
            successThreshold: 2        # Re-add only after 2 successes

          startupProbe:                # Prevents liveness killing slow-starting containers
            httpGet:
              path: /livez
              port: 8080
            failureThreshold: 30       # 30 × 10s = 5 minutes to start
            periodSeconds: 10
```

**Startup probe:** Use when the service takes > 30 seconds to initialize (e.g., loading large ML models, warming up caches). Disables liveness probe until startup completes.

---

## Exclusion from Distributed Tracing

Health checks generate trace noise and skew latency percentiles. Exclude them.

**OTel Collector (filter processor):**
```yaml
processors:
  filter/exclude_health:
    traces:
      span:
        - 'attributes["http.target"] == "/livez"'
        - 'attributes["http.target"] == "/readyz"'
        - 'attributes["url.path"] == "/livez"'
        - 'attributes["url.path"] == "/readyz"'
```

**Datadog agent (datadog.yaml):**
```yaml
apm_config:
  ignore_resources:
    - "GET /livez"
    - "GET /readyz"
    - "GET /healthz"
```

**Go — exclude at SDK level (before Collector):**
```go
// gin-specific: don't instrument health routes
r := gin.New()
r.GET("/livez", livenessHandler)   // registered BEFORE otelgin middleware
r.GET("/readyz", readinessHandler)  // registered BEFORE otelgin middleware
r.Use(otelgin.Middleware("order-service"))
// ... other routes
```

**Node.js (Express):**
```javascript
// Register health routes before OTel middleware
app.get('/livez', livenessHandler);
app.get('/readyz', readinessHandler);
app.use(otelExpressMiddleware());  // only applied to routes after this
```

---

## Dependency Check Timeout Guidelines

| Dependency | Recommended Timeout | Notes |
|------------|---------------------|-------|
| Primary database | 2s | Fail fast; if DB is slow, pod is not ready |
| Read replica | 1s | Non-critical path |
| Redis/Memcached | 500ms | In-memory should be near-instant |
| Downstream HTTP service | 3s | Depends on that service's SLA |
| Message broker | 2s | Kafka/RabbitMQ health |

**Never check** in readiness: external third-party APIs (payment gateways, email providers), cold-start conditions that resolve on their own.

---

## Anti-Patterns

| Avoid | Why | Instead |
|-------|-----|---------|
| Database check in liveness probe | DB outage causes pod restarts instead of traffic removal | Database in readiness only |
| No timeout on dependency checks | Slow dependency hangs the health check | Always use context with timeout |
| Returning 200 from /readyz on DB failure | Keeps pod in LB rotation while broken | Return 503 on any critical dep failure |
| Returning body-level error with 200 status | Kubernetes uses HTTP status, not body | Use HTTP status 503 for failures |
| Including health endpoints in traces | Skews latency P99, generates noise | Exclude in Collector or agent config |
| Same handler for /livez and /readyz | Confuses K8s probe semantics | Separate handlers, separate logic |
