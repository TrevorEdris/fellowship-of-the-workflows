# Cardinality Guide

## What Is Cardinality

**Cardinality** = the number of unique time series produced by a metric.

In Prometheus, each unique combination of label values creates a separate time series. Cardinality determines storage cost, query performance, and Prometheus memory usage.

In Datadog, cardinality determines the number of unique custom metric billing units (called "custom metrics"), with a practical budget of 350 unique tag combinations per metric before billing impact becomes significant.

---

## Cardinality Math

**Formula:**
```
unique_time_series = product(distinct_values_per_label)
```

**Example — building up a metric:**

```
metric: http_request_duration_seconds

Step 1: No labels
  = 1 histogram × 12 series (10 buckets + _count + _sum)
  = 12 time series

Step 2: Add method label (5 values: GET, POST, PUT, PATCH, DELETE)
  = 12 × 5 = 60 time series

Step 3: Add status_code label (8 values: 200, 201, 400, 401, 403, 404, 422, 500)
  = 60 × 8 = 480 time series

Step 4: Add route label (20 distinct routes)
  = 480 × 20 = 9,600 time series

Step 5: Add user_id label (100,000 users)
  = 9,600 × 100,000 = 960,000,000 time series ← [CRITICAL]
```

---

## Safe vs Dangerous Labels

### Safe Labels (bounded, low cardinality)

| Label | Typical Value Count | Examples |
|-------|---------------------|---------|
| `method` | 5–8 | GET, POST, PUT, DELETE, PATCH |
| `status_code` | 10–15 | 200, 201, 400, 404, 500 |
| `status_class` | 4 | 2xx, 3xx, 4xx, 5xx |
| `route` | 10–100 | `/users/{id}`, `/orders`, `/health` |
| `env` | 3–5 | production, staging, dev |
| `region` | 5–15 | us-east-1, eu-west-1 |
| `service` | < 100 | order-service, payment-service |
| `version` | < 20 | 1.0.0, 1.0.1 (but be careful with rapid releases) |
| `db_name` | < 20 | orders, users, inventory |
| `queue` | < 50 | order-created, payment-processed |
| `tier` | 3–5 | free, pro, enterprise |
| `feature_flag` | < 20 | Known flags only |

### Dangerous Labels (unbounded or near-unbounded)

| Label | Why Dangerous | Alternative |
|-------|---------------|------------|
| `user_id` | Millions of users | Omit; use `tier` or `cohort` |
| `request_id` | Unique per request | Omit entirely from metrics |
| `trace_id` | Unique per trace | Use in logs/spans, not metrics |
| `session_id` | Unique per session | Omit |
| `url` | Full URLs include query strings | Use `route` template |
| `ip_address` | Source IP is effectively unbounded | Omit or bin to subnet |
| `hostname` | Individual pod names (Kubernetes) | Use `service` + `region` |
| `error_message` | Unique messages per error | Use `error_type` (enum) |
| `sql_query` | Unique text per query | Use `operation` + `table` |
| `customer_id` | Unbounded in B2B | Use `customer_tier` |
| `version` (rapid CI/CD) | New version per commit = cardinality explosion | Bin to major.minor only |

---

## Prometheus Cardinality Limits

**Recommended thresholds:**

| Metric | Max Time Series | Action at Limit |
|--------|----------------|-----------------|
| Single histogram | < 10,000 | Review labels |
| Single counter | < 5,000 | Review labels |
| Total per service | < 100,000 | Audit all metrics |
| Total Prometheus | < 10M | Scale or archive |

**Detecting high-cardinality metrics in Prometheus:**
```promql
# Top 10 metrics by time series count
topk(10, count by (__name__)({__name__=~".+"}))

# Series count for a specific metric
count(http_request_duration_seconds_bucket)

# Labels and their value counts for a metric
count by (method, status_code, route) (http_request_duration_seconds_bucket)
```

---

## Datadog Cardinality Budget

**350 unique tag combinations** is the practical billing threshold per custom metric. Beyond this, each additional unique combination is billed separately.

**Budget calculation:**
```
tag combinations = product(distinct_values_per_tag)

Example:
  env (3) × status_code (8) × route (15) = 360 combinations
  → Slightly over budget; consider collapsing status_code to status_class (4 values)

  env (3) × status_class (4) × route (15) = 180 combinations
  → Safe
```

**Strategies to stay within budget:**

1. **Group status codes:** Use `2xx`, `4xx`, `5xx` instead of individual codes
2. **Limit route granularity:** Instrument only the top-N routes by volume; group the rest as `other`
3. **Use separate metrics per high-cardinality dimension:** Instead of one metric with `env` + `service` + `region`, emit tagged metrics and rely on Datadog's tag filtering
4. **Monitor your custom metric count:** Check Datadog's Usage → Custom Metrics dashboard monthly

---

## Mitigation Strategies

### Prometheus — Relabeling (Drop at Collector)

Drop high-cardinality labels before storing in Prometheus:

```yaml
# OTel Collector — transform processor to drop or aggregate labels
processors:
  transform/drop_user_id:
    metric_statements:
      - context: datapoint
        statements:
          - delete_key(attributes, "user_id")
          - delete_key(attributes, "request_id")

  # Or: use filter to drop entire metric if it escapes
  filter/drop_debug_metrics:
    metrics:
      metric:
        - name == "http_request_duration_debug_seconds"
```

### Prometheus — Recording Rules (Pre-Aggregate)

Aggregate high-cardinality metrics into lower-cardinality recorded metrics:

```yaml
groups:
  - name: precomputed
    interval: 60s
    rules:
      # Pre-aggregate: drop route label, keep only method + status_class
      - record: job:http_requests:rate5m
        expr: |
          sum by (job, method, status_class) (
            rate(http_requests_total[5m])
          )

      # Pre-aggregate latency percentiles (removes all labels except service)
      - record: service:http_request_duration_p99:5m
        expr: |
          histogram_quantile(0.99, sum by (service, le) (
            rate(http_request_duration_seconds_bucket[5m])
          ))
```

### Prometheus — Drop Rules (Metric-Level)

Drop entire metrics that shouldn't be stored (e.g., debug metrics in production):

```yaml
# In Prometheus scrape config:
scrape_configs:
  - job_name: order-service
    metric_relabel_configs:
      # Drop any metric with user_id label
      - source_labels: [user_id]
        regex: ".+"
        action: drop
      # Drop debug metrics entirely
      - source_labels: [__name__]
        regex: ".*_debug_.*"
        action: drop
```

### Datadog — Tag Limiting

```javascript
// DogStatsD — explicitly limit tag cardinality
function getStatusClass(statusCode) {
  if (statusCode < 300) return '2xx';
  if (statusCode < 400) return '3xx';
  if (statusCode < 500) return '4xx';
  return '5xx';
}

client.increment('http.requests', 1, [
  `env:${process.env.DD_ENV}`,
  `service:${process.env.DD_SERVICE}`,
  `status_class:${getStatusClass(res.statusCode)}`,  // not status_code
  `route:${routeTemplate}`,                           // not req.url
]);
```

---

## Cardinality Audit Checklist

Run this audit before adding any new label to an existing metric:

1. **Count existing time series:**
   ```promql
   count(your_metric_name)
   ```

2. **Estimate new cardinality:**
   ```
   current_count × distinct_values_of_new_label
   ```

3. **Check against limit (10,000 for histograms, 5,000 for counters)**

4. **If over limit:** use one of the mitigation strategies above

5. **Document the decision** in the metric's accompanying code comment

---

## Anti-Patterns Summary

| Anti-Pattern | Cardinality Impact | Fix |
|-------------|-------------------|-----|
| `user_id` as label | O(users) per metric | Omit |
| `url` as label (raw path) | O(unique URLs) | Use route template |
| `error_message` as label | O(unique errors) | Use `error_type` enum |
| `hostname` in K8s | O(pods) | Use `service` + `region` |
| `version` = git SHA | O(commits) | Use semver major.minor |
| Histogram with 5+ labels | Exponential explosion | Keep histograms to ≤ 3 labels |
| Label value from user input | Unbounded | Validate against allowlist |
| Different label names for same concept | Hard to query | Standardize: always `status_code`, `route` |
