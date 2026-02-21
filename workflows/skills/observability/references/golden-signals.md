# Golden Signals Reference

## The Three Frameworks

### RED Method (Microservices)

Caller perspective — what the user of a service experiences.

| Signal | Description | Primary Use |
|--------|-------------|-------------|
| **R**ate | Requests per second | Is the service receiving traffic? |
| **E**rrors | Failed requests per second | Are requests failing? |
| **D**uration | Latency distribution (P50/P95/P99) | How slow are requests? |

### USE Method (Infrastructure)

Resource perspective — how are infrastructure components behaving.

| Signal | Description | Example Resources |
|--------|-------------|------------------|
| **U**tilization | % of time resource is busy | CPU, disk I/O |
| **S**aturation | Extra work queued beyond capacity | Run queue length, memory swap |
| **E**rrors | Error events for the resource | Network errors, disk errors |

### Google's Four Golden Signals (Broadest Scope)

| Signal | Description | Alert When |
|--------|-------------|------------|
| **Latency** | Time to serve a request (success vs failure separately) | P99 > SLO threshold |
| **Traffic** | Demand on the system (req/s, transactions/s) | Anomalous drop or spike |
| **Errors** | Rate of failed requests (explicit 5xx + implicit wrong results) | > 0.1% of requests |
| **Saturation** | How "full" the service is (CPU, memory, queue depth) | Queue depth rising unbounded |

**Relationship:** RED ⊂ Four Golden Signals. USE complements both at the infrastructure layer.
- Page on Golden Signals (user-visible impact)
- Investigate with RED (service-level detail)
- Diagnose with USE (resource-level root cause)

---

## PromQL Queries

### Rate (Requests per Second)

```promql
# Total request rate over 5-minute window
sum(rate(http_requests_total{service="$service", env="$env"}[5m]))

# Request rate by status class
sum by (status_class) (
  label_replace(
    rate(http_requests_total{service="$service"}[5m]),
    "status_class",
    "${1}xx",
    "status_code",
    "([0-9]).*"
  )
)
```

### Errors (Error Rate)

```promql
# Error rate (ratio of 5xx to total)
sum(rate(http_requests_total{service="$service", status_code=~"5.."}[5m]))
/
sum(rate(http_requests_total{service="$service"}[5m]))

# Error rate percentage
(
  sum(rate(http_requests_total{service="$service", status_code=~"5.."}[5m]))
  /
  sum(rate(http_requests_total{service="$service"}[5m]))
) * 100

# Absolute error count per second
sum(rate(http_requests_total{service="$service", status_code=~"5.."}[5m]))
```

### Duration (Latency Percentiles)

```promql
# P50 latency
histogram_quantile(0.50, sum by (le) (
  rate(http_request_duration_seconds_bucket{service="$service"}[5m])
))

# P95 latency
histogram_quantile(0.95, sum by (le) (
  rate(http_request_duration_seconds_bucket{service="$service"}[5m])
))

# P99 latency
histogram_quantile(0.99, sum by (le) (
  rate(http_request_duration_seconds_bucket{service="$service"}[5m])
))

# Latency broken down by route
histogram_quantile(0.99, sum by (le, route) (
  rate(http_request_duration_seconds_bucket{service="$service"}[5m])
))
```

### Saturation

```promql
# CPU utilization
1 - avg(rate(node_cpu_seconds_total{mode="idle", instance=~"$instance"}[5m]))

# Memory utilization
1 - (
  node_memory_MemAvailable_bytes{instance=~"$instance"}
  /
  node_memory_MemTotal_bytes{instance=~"$instance"}
)

# Active HTTP connections (from OTel UpDownCounter)
sum(http_server_active_requests{service="$service"})

# Queue depth
sum(queue_depth{service="$service", queue="$queue"})
```

---

## Datadog Query Equivalents

### Rate

```
# Requests per second
sum:http.server.requests{service:$service,env:$env}.as_rate()

# Rate by status code group
sum:http.server.requests{service:$service} by {status_code}.as_rate()
```

### Errors

```
# Error rate
sum:http.server.requests.errors{service:$service,env:$env}.as_rate()
/
sum:http.server.requests{service:$service,env:$env}.as_rate()

# As percentage
(sum:http.server.requests.errors{service:$service}.as_rate()
 /
 sum:http.server.requests{service:$service}.as_rate()) * 100
```

### Duration (Latency)

```
# P95 latency using distribution metric
p95:http.server.request.duration{service:$service,env:$env}

# P99 latency
p99:http.server.request.duration{service:$service,env:$env}

# Latency by endpoint
p95:http.server.request.duration{service:$service} by {endpoint}
```

### Saturation

```
# CPU utilization (from host integration)
avg:system.cpu.user{host:$host} + avg:system.cpu.system{host:$host}

# Memory utilization
(avg:system.mem.total{host:$host} - avg:system.mem.usable{host:$host})
/ avg:system.mem.total{host:$host} * 100

# Queue depth
avg:myservice.queue.depth{service:$service,queue:$queue}
```

---

## Grafana Panel Configuration

### Rate Panel (Time Series)

```json
{
  "title": "Request Rate (req/s)",
  "type": "timeseries",
  "fieldConfig": {
    "defaults": { "unit": "reqps" }
  },
  "targets": [{
    "expr": "sum(rate(http_requests_total{service=\"$service\"}[5m])) by (route)",
    "legendFormat": "{{route}}"
  }]
}
```

### Error Rate Panel (Stat — highlight red when > 1%)

```json
{
  "title": "Error Rate",
  "type": "stat",
  "fieldConfig": {
    "defaults": {
      "unit": "percentunit",
      "thresholds": {
        "steps": [
          {"color": "green", "value": null},
          {"color": "yellow", "value": 0.005},
          {"color": "red", "value": 0.01}
        ]
      }
    }
  },
  "targets": [{
    "expr": "sum(rate(http_requests_total{service=\"$service\",status_code=~\"5..\"}[5m])) / sum(rate(http_requests_total{service=\"$service\"}[5m]))"
  }]
}
```

### Latency Heatmap Panel

```json
{
  "title": "Request Duration Heatmap",
  "type": "heatmap",
  "targets": [{
    "expr": "sum(rate(http_request_duration_seconds_bucket{service=\"$service\"}[5m])) by (le)",
    "legendFormat": "{{le}}",
    "format": "heatmap"
  }]
}
```

---

## Alert Thresholds by Signal Type

| Signal | Page Threshold | Warn Threshold | Window |
|--------|---------------|----------------|--------|
| Error rate | > 1% | > 0.5% | 5m |
| P99 latency | > 1s | > 500ms | 5m |
| P95 latency | > 500ms | > 300ms | 5m |
| Queue depth | > capacity × 0.8 | > capacity × 0.5 | 2m |
| SLO burn rate | > 14x | > 5x | 1h / 6h |

---

## Signal Priority for On-Call

1. **Error rate** — highest direct user impact; page immediately at > 1%
2. **P99 latency** — second most user-visible; page at > 1s
3. **Traffic drop** — sudden 50%+ drop may indicate outage or mis-deployment; page
4. **Saturation** — rising queue depth is leading indicator; ticket when > 80% capacity
5. **CPU/memory** — investigate only, never page; they are causes, not symptoms
