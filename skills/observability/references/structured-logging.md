# Structured Logging Reference

## Required JSON Fields

Every log line must include these fields:

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `timestamp` | string (ISO 8601 UTC) | Yes | `2026-02-20T10:30:00.000Z` |
| `level` | string | Yes | `error`, `warn`, `info`, `debug` — lowercase |
| `message` | string | Yes | Human-readable description |
| `service` | string | Yes | Matches `OTEL_SERVICE_NAME` or `DD_SERVICE` |

**Trace correlation fields — OTel:**

| Field | Type | Format | Notes |
|-------|------|--------|-------|
| `trace_id` | string | 32 hex chars | `4bf92f3577b34da6a3ce929d0e0e4736` |
| `span_id` | string | 16 hex chars | `00f067aa0ba902b7` |
| `trace_flags` | string | 2 hex chars | `01` (sampled) or `00` (not sampled) |

**Trace correlation fields — Datadog:**

| Field | Type | Format | Notes |
|-------|------|--------|-------|
| `dd.trace_id` | string | decimal integer | `7277407061855694098` — NOT hex |
| `dd.span_id` | string | decimal integer | `113750223261052439` — NOT hex |
| `dd.service` | string | service name | Must match `DD_SERVICE` |
| `dd.env` | string | environment | Must match `DD_ENV` |
| `dd.version` | string | version | Must match `DD_VERSION` |

**Critical difference:** OTel trace IDs are hexadecimal. Datadog trace IDs are decimal. Using hex in a Datadog log pipeline will break trace-log correlation.

---

## OTel Format Example

```json
{
  "timestamp": "2026-02-20T10:30:00.000Z",
  "level": "error",
  "message": "Failed to process order: payment gateway timeout",
  "service": "order-service",
  "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736",
  "span_id": "00f067aa0ba902b7",
  "trace_flags": "01",
  "order_id": "ord_abc123",
  "error_type": "PaymentGatewayTimeout"
}
```

## Datadog Format Example

```json
{
  "timestamp": "2026-02-20T10:30:00.000Z",
  "level": "error",
  "message": "Failed to process order: payment gateway timeout",
  "dd.service": "order-service",
  "dd.env": "production",
  "dd.version": "1.2.3",
  "dd.trace_id": "7277407061855694098",
  "dd.span_id": "113750223261052439",
  "order_id": "ord_abc123",
  "error_type": "PaymentGatewayTimeout"
}
```

---

## Per-Language Trace Correlation Injection

### Go — OTel with Zap

```go
import (
    "go.opentelemetry.io/contrib/bridges/otelzap"
    "go.opentelemetry.io/otel/log/global"
    "go.uber.org/zap"
    "go.uber.org/zap/zapcore"
)

// Option 1: OTel log bridge (auto-injects trace context)
loggerProvider := global.GetLoggerProvider()
core := otelzap.NewCore("order-service", otelzap.WithLoggerProvider(loggerProvider))
logger := zap.New(core)

// Use with context to get automatic trace injection:
logger.InfoContext(ctx, "order created",
    zap.String("order_id", orderID),
)
```

```go
// Option 2: Manual zap fields (when OTel log bridge not available)
import "go.opentelemetry.io/otel/trace"

func traceFields(ctx context.Context) []zap.Field {
    span := trace.SpanFromContext(ctx)
    sc := span.SpanContext()
    if !sc.IsValid() {
        return nil
    }
    return []zap.Field{
        zap.String("trace_id", sc.TraceID().String()),
        zap.String("span_id", sc.SpanID().String()),
        zap.String("trace_flags", sc.TraceFlags().String()),
    }
}

// Usage:
logger.Info("order created", append(traceFields(ctx), zap.String("order_id", id))...)
```

### Go — Datadog with Zap

```go
import (
    "gopkg.in/DataDog/dd-trace-go.v1/ddtrace/tracer"
    "go.uber.org/zap"
)

func ddTraceFields(ctx context.Context) []zap.Field {
    span, ok := tracer.SpanFromContext(ctx)
    if !ok {
        return nil
    }
    return []zap.Field{
        zap.Uint64("dd.trace_id", span.Context().TraceID()),
        zap.Uint64("dd.span_id", span.Context().SpanID()),
        zap.String("dd.service", os.Getenv("DD_SERVICE")),
        zap.String("dd.env", os.Getenv("DD_ENV")),
        zap.String("dd.version", os.Getenv("DD_VERSION")),
    }
}
```

### Node.js — OTel with Pino

```javascript
// pino-opentelemetry-transport handles injection automatically
const pino = require('pino');

const logger = pino({
  level: 'info',
  transport: {
    target: 'pino-opentelemetry-transport',
  },
});

// Or manual injection:
const { trace, context } = require('@opentelemetry/api');

function getTraceContext() {
  const span = trace.getActiveSpan();
  if (!span) return {};
  const ctx = span.spanContext();
  return {
    trace_id: ctx.traceId,
    span_id: ctx.spanId,
    trace_flags: ctx.traceFlags.toString(16).padStart(2, '0'),
  };
}

logger.info({ ...getTraceContext(), order_id: '123' }, 'order created');
```

### Node.js — Datadog with Pino

```javascript
// dd-trace with logInjection: true handles pino/winston/bunyan automatically
const tracer = require('dd-trace').init({
  logInjection: true,  // auto-injects dd.trace_id, dd.span_id into all supported loggers
});

const logger = require('pino')();
// dd.trace_id and dd.span_id are now injected automatically on every log
logger.info({ order_id: '123' }, 'order created');
```

```javascript
// Manual injection when logInjection can't be used:
const tracer = require('dd-trace');

function getDDTraceContext() {
  const span = tracer.scope().active();
  if (!span) return {};
  const ctx = span.context();
  return {
    'dd.trace_id': ctx.toTraceId(),   // decimal string
    'dd.span_id': ctx.toSpanId(),     // decimal string
    'dd.service': process.env.DD_SERVICE,
    'dd.env': process.env.DD_ENV,
    'dd.version': process.env.DD_VERSION,
  };
}
```

### Python — OTel with structlog

```python
import structlog
from opentelemetry import trace as otel_trace

def add_otel_trace_context(logger, method, event_dict):
    span = otel_trace.get_current_span()
    ctx = span.get_span_context()
    if ctx.is_valid:
        event_dict["trace_id"] = format(ctx.trace_id, "032x")
        event_dict["span_id"] = format(ctx.span_id, "016x")
        event_dict["trace_flags"] = format(ctx.trace_flags, "02x")
    return event_dict

structlog.configure(
    processors=[
        add_otel_trace_context,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.JSONRenderer(),
    ]
)
log = structlog.get_logger()
log.info("order_created", order_id="ord_123")
```

### Python — Datadog with structlog

```python
import structlog
import ddtrace
from ddtrace import tracer as dd_tracer
import os

def add_dd_trace_context(logger, method, event_dict):
    span = dd_tracer.current_span()
    if span:
        ctx = span.context
        event_dict["dd.trace_id"] = str(ctx.trace_id)    # decimal
        event_dict["dd.span_id"] = str(ctx.span_id)      # decimal
        event_dict["dd.service"] = os.environ.get("DD_SERVICE", "")
        event_dict["dd.env"] = os.environ.get("DD_ENV", "")
        event_dict["dd.version"] = os.environ.get("DD_VERSION", "")
    return event_dict
```

### Rust — OTel with tracing-subscriber

```rust
use opentelemetry::trace::TraceContextExt;
use tracing_opentelemetry::OpenTelemetrySpanExt;
use tracing_subscriber::{layer::SubscriberExt, util::SubscriberInitExt, EnvFilter, Registry};
use tracing_subscriber::fmt::format::FmtSpan;

Registry::default()
    .with(EnvFilter::from_default_env())
    .with(
        tracing_subscriber::fmt::layer()
            .json()
            .with_span_events(FmtSpan::CLOSE)
            .with_current_span(true)  // includes trace_id, span_id in JSON output
    )
    .with(tracing_opentelemetry::layer())
    .init();

// Usage — trace_id/span_id automatically included in JSON output:
tracing::info!(order_id = %order_id, "order created");
```

---

## Sensitive Data — What NOT to Log

Never log the following fields regardless of log level:

| Category | Examples |
|----------|---------|
| Authentication | Passwords, API keys, JWT tokens, session tokens, OAuth codes |
| Payment | Full card numbers, CVV, bank account numbers |
| PII | Social security numbers, full date of birth, raw email addresses (if regulated) |
| Secrets | Private keys, database connection strings with credentials |
| Request/response bodies | Unless explicitly sanitized and reviewed for compliance |

For debugging, log entity identifiers (`user_id`, `order_id`) rather than entity content.

---

## Log Level Guidelines

| Level | When to Use | Examples |
|-------|-------------|---------|
| `error` | Request failed, operation cannot be retried, data corrupted | DB connection failed, payment declined (from gateway), panic recovery |
| `warn` | Recoverable issue, degraded operation, approaching limit | Retry succeeded after 2 attempts, cache miss causing slow path, rate limit warning |
| `info` | Business-significant events, state transitions | Order created, user authenticated, job completed, deployment started |
| `debug` | Developer context, request/response details (never in prod by default) | SQL query text, HTTP headers, intermediate computed values |
| `trace` | Granular internal flow (disable in production) | Loop iterations, lock acquisitions |

**Default production log level: `info`**. Set `debug` only for a specific service during active incident investigation, then revert.

---

## Log Sampling

For high-throughput services (> 10k req/s), log sampling prevents log cost explosion:

```go
// Go — sample debug logs at 1%
if rand.Float64() < 0.01 {
    logger.Debug("request detail", zap.Any("headers", req.Header))
}

// Always log errors without sampling:
if err != nil {
    logger.Error("request failed", zap.Error(err))  // no sampling gate
}
```

**Rule:** Never sample `error` or `warn` level logs. Sample only `debug` and `trace`.
