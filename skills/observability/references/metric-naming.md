# Metric Naming Reference

## Prometheus Naming Rules

**Pattern:** `{namespace}_{subsystem}_{name}_{unit}`

All parts use `snake_case`. Namespace and subsystem are optional but strongly recommended for library and application metrics.

| Component | Description | Example |
|-----------|-------------|---------|
| `namespace` | Application or org prefix | `http`, `myapp`, `grpc` |
| `subsystem` | Component or module | `server`, `client`, `db` |
| `name` | What is measured | `requests`, `duration`, `bytes` |
| `unit` | Base unit suffix | `_seconds`, `_bytes`, `_total` |

**Full examples:**
```
http_server_requests_total
http_server_request_duration_seconds
db_query_duration_seconds
grpc_client_calls_total
process_memory_usage_bytes
```

---

## Metric Type Decision Guide

| Signal | Prometheus Type | OTel Instrument | Rationale |
|--------|----------------|----------------|-----------|
| Request count | Counter | Counter | Monotonically increasing |
| Error count | Counter | Counter | Monotonically increasing |
| Latency distribution | Histogram | Histogram | Need percentiles; supports exemplars |
| Payload size | Histogram | Histogram | Distribution matters |
| Active connections | Gauge | UpDownCounter | Goes up and down |
| Queue depth | Gauge | UpDownCounter | Goes up and down |
| Memory usage | Gauge | ObservableGauge | Point-in-time snapshot |
| CPU utilization | Gauge | ObservableGauge | Point-in-time snapshot |
| Cache hit ratio | Gauge (derived) | ObservableGauge | Computed from counters |

**Never use Summary for latency** — Summaries pre-aggregate per instance and cannot be aggregated across multiple instances in Prometheus. Always use Histogram.

---

## Unit Conventions

**Always use base units.** Do not use scaled variants.

| Correct | Incorrect | Why |
|---------|-----------|-----|
| `_seconds` | `_milliseconds`, `_ms` | Seconds is the SI base unit for time |
| `_bytes` | `_kilobytes`, `_kb`, `_megabytes` | Bytes is the base unit |
| `_ratio` | `_percent`, `_pct` | Ratios are dimensionless 0.0–1.0 |
| `_celsius` | `_fahrenheit` | SI standard |
| (no unit suffix for counts) | `_count` in name | Counter implies count; suffix is `_total` |

**Histogram naming — no `_bucket`, `_count`, `_sum` suffix in the registered name:**
```
# Register as:
http_request_duration_seconds

# Prometheus automatically creates:
http_request_duration_seconds_bucket{le="0.1"}
http_request_duration_seconds_count
http_request_duration_seconds_sum
```

---

## Counter Rules

- Name must end with `_total`
- Never reset a counter (use a new metric name if process restarts; Prometheus handles rate() correctly)
- Pair with `rate()` in PromQL for per-second rate

```promql
# Requests per second over 5m window
rate(http_server_requests_total[5m])

# Error rate
rate(http_server_requests_total{status_code=~"5.."}[5m])
  / rate(http_server_requests_total[5m])
```

---

## Label Naming

- Use `snake_case` for label names
- Use consistent names across metrics: if one metric has `status_code`, all related metrics should use `status_code` not `http_status` or `code`
- Standard label names (follow these for HTTP metrics):

| Label | Values | Notes |
|-------|--------|-------|
| `method` | GET, POST, PUT, DELETE, PATCH | Uppercase |
| `status_code` | 200, 201, 400, 404, 500 | Numeric string |
| `route` | `/users/{id}`, `/orders` | Template, not actual path |
| `service` | `order-service` | Lowercase hyphenated |
| `env` | `production`, `staging`, `dev` | Lowercase |
| `region` | `us-east-1`, `eu-west-1` | Cloud region |

---

## Datadog Naming Rules

Datadog uses **dot notation** instead of underscore-separated names.

**Pattern:** `{service}.{subsystem}.{metric_name}`

```
order.service.requests               # counter
order.service.request.duration       # distribution (milliseconds OK for Datadog)
order.db.query.duration              # database query time
order.cache.hits                     # cache hit counter
order.cache.misses                   # cache miss counter
```

**Differences from Prometheus:**
- No `_total` suffix on counters — Datadog handles cumulative vs rate in queries
- Milliseconds are acceptable (Datadog stores in ms internally)
- Tags replace label cardinality — keep the metric name shorter, push dimensions to tags
- Dot separators, not underscores

---

## Examples by Language

**Go:**
```go
// Prometheus (via OTel SDK)
meter := otel.Meter("github.com/myorg/order-service")
requestsTotal, _ := meter.Int64Counter("http.server.requests",
    metric.WithDescription("Total HTTP requests"),
    metric.WithUnit("{request}"),
)
requestDuration, _ := meter.Float64Histogram("http.server.request.duration",
    metric.WithDescription("HTTP request duration"),
    metric.WithUnit("s"),
    metric.WithExplicitBucketBoundaries(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10),
)
```

**Python:**
```python
from opentelemetry import metrics

meter = metrics.get_meter("order_service", version="1.0.0")
requests_counter = meter.create_counter(
    name="http.server.requests",
    description="Total HTTP requests",
    unit="{request}",
)
request_duration = meter.create_histogram(
    name="http.server.request.duration",
    description="HTTP request duration in seconds",
    unit="s",
)
```

**Node.js:**
```javascript
const { metrics } = require('@opentelemetry/api');
const meter = metrics.getMeter('order-service', '1.0.0');

const requestCounter = meter.createCounter('http.server.requests', {
  description: 'Total HTTP requests',
  unit: '{request}',
});

const requestDuration = meter.createHistogram('http.server.request.duration', {
  description: 'HTTP request duration in seconds',
  unit: 's',
  advice: {
    explicitBucketBoundaries: [0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10],
  },
});
```

---

## Anti-Patterns

| Avoid | Why | Instead |
|-------|-----|---------|
| `requests_counter` | Redundant type in name | `requests_total` |
| `latency_ms` | Not base unit | `duration_seconds` |
| `http_request_duration_seconds_histogram` | Type suffix in name | `http_request_duration_seconds` |
| `error_percentage` | Not base unit | `errors_total` + compute rate() |
| `user_id` as label | Unbounded cardinality | Omit; aggregate by tier instead |
| `url` or `path` as label | Unbounded cardinality | `route` (template only) |
