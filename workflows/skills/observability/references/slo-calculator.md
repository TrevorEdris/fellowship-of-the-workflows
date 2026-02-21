# SLO Calculator Reference

## Error Budget Table

Error budget = `(1 - SLO_target) × window_duration`

| SLO Target | Monthly Budget | Weekly Budget | Daily Budget | Notes |
|------------|---------------|---------------|--------------|-------|
| 99.0% | 432.0 min (7.2h) | 100.8 min | 14.4 min | Suitable for non-critical internal tools |
| 99.5% | 216.0 min (3.6h) | 50.4 min | 7.2 min | Typical internal API |
| 99.9% | 43.2 min | 10.1 min | 1.44 min | Standard production service |
| 99.95% | 21.6 min | 5.0 min | 43.2 sec | Critical platform service |
| 99.99% | 4.32 min | 1.01 min | 8.64 sec | Payment, auth, core API |
| 99.999% | 25.9 sec | 6.05 sec | 0.864 sec | Rarely achievable without full redundancy |

**Starting point recommendation:** 99.9% for new services. Tighten after measuring actual reliability.

---

## SLI Formulas (PromQL)

### Availability SLI

```promql
# Ratio of successful requests to total requests (28-day rolling window)
sum(rate(http_requests_total{service="$service", env="$env", status_code!~"5.."}[28d]))
/
sum(rate(http_requests_total{service="$service", env="$env"}[28d]))
```

```promql
# Availability as percentage for reporting
(
  sum(rate(http_requests_total{service="$service",status_code!~"5.."}[28d]))
  /
  sum(rate(http_requests_total{service="$service"}[28d]))
) * 100
```

### Latency SLI (% requests under threshold)

```promql
# % of requests completing in < 300ms (suitable for 99th percentile SLO)
sum(rate(http_request_duration_seconds_bucket{service="$service",le="0.3"}[28d]))
/
sum(rate(http_request_duration_seconds_count{service="$service"}[28d]))
```

```promql
# % of requests completing in < 1s
sum(rate(http_request_duration_seconds_bucket{service="$service",le="1.0"}[28d]))
/
sum(rate(http_request_duration_seconds_count{service="$service"}[28d]))
```

### Error Rate SLI

```promql
# Error rate over 5-minute window (for alerting, not SLO tracking)
sum(rate(http_requests_total{service="$service",status_code=~"5.."}[5m]))
/
sum(rate(http_requests_total{service="$service"}[5m]))
```

### Composite SLI (availability AND latency)

```promql
# Both conditions must be true: request is successful AND completes in < 300ms
# Use histogram approach: count requests in bucket with good status
sum(rate(http_request_duration_seconds_bucket{service="$service",status_code!~"5..",le="0.3"}[28d]))
/
sum(rate(http_request_duration_seconds_count{service="$service"}[28d]))
```

---

## Burn Rate Explained

**Burn rate** = how fast the error budget is being consumed relative to the SLO window.

```
Burn rate = (current_error_rate / SLO_error_rate)
         = current_error_rate / (1 - SLO_target)
```

**Example (99.9% SLO, monthly window):**
- Error budget: 43.2 minutes per month
- At 1x burn rate: budget exhausted in exactly 30 days
- At 14x burn rate: budget exhausted in 30 / 14 ≈ 2.1 days
- At 5x burn rate: budget exhausted in 30 / 5 = 6 days

**PromQL burn rate formula:**

```promql
# 1-hour burn rate
(
  sum(rate(http_requests_total{service="$service",status_code=~"5.."}[1h]))
  /
  sum(rate(http_requests_total{service="$service"}[1h]))
) / (1 - 0.999)
```

---

## Multi-Window Burn Rate AlertManager Rules

Multi-window alerting prevents both alert fatigue (short spikes trigger false pages) and missed slow degradations.

```yaml
groups:
  - name: slo-burn-rate-$service
    interval: 30s
    rules:
      # Recording rules for efficiency (compute once, alert on result)
      - record: slo:http_requests:error_rate1h
        expr: |
          sum(rate(http_requests_total{service="$service",status_code=~"5.."}[1h]))
          / sum(rate(http_requests_total{service="$service"}[1h]))

      - record: slo:http_requests:error_rate5h
        expr: |
          sum(rate(http_requests_total{service="$service",status_code=~"5.."}[5h]))
          / sum(rate(http_requests_total{service="$service"}[5h]))

      - record: slo:http_requests:error_rate6h
        expr: |
          sum(rate(http_requests_total{service="$service",status_code=~"5.."}[6h]))
          / sum(rate(http_requests_total{service="$service"}[6h]))

      - record: slo:http_requests:error_rate30d
        expr: |
          sum(rate(http_requests_total{service="$service",status_code=~"5.."}[30d]))
          / sum(rate(http_requests_total{service="$service"}[30d]))

      # Fast burn: 14x for 1h → page immediately
      - alert: SLOFastBurn
        expr: |
          slo:http_requests:error_rate1h{service="$service"} > (14 * (1 - 0.999))
          and
          slo:http_requests:error_rate5h{service="$service"} > (14 * (1 - 0.999))
        for: 2m
        labels:
          severity: page
          slo: availability
          service: $service
        annotations:
          summary: "Fast SLO burn: {{ $labels.service }} at 14x burn rate"
          description: "Error rate {{ $value | humanizePercentage }} over last hour. Error budget will exhaust in ~2 days."
          runbook: "https://wiki/runbooks/{{ $labels.service }}-slo-burn"

      # Slow burn: 5x for 6h → create ticket
      - alert: SLOSlowBurn
        expr: |
          slo:http_requests:error_rate6h{service="$service"} > (5 * (1 - 0.999))
          and
          slo:http_requests:error_rate30d{service="$service"} > (5 * (1 - 0.999))
        for: 15m
        labels:
          severity: ticket
          slo: availability
          service: $service
        annotations:
          summary: "Slow SLO burn: {{ $labels.service }} at 5x burn rate"
          description: "Error rate {{ $value | humanizePercentage }} over last 6h. Error budget will exhaust in ~6 days."
          runbook: "https://wiki/runbooks/{{ $labels.service }}-slo-burn"
```

---

## Multi-Window Burn Rate — Datadog API JSON

Create the SLO via `POST /api/v1/slo`:

```json
{
  "name": "{service} Availability SLO ({env})",
  "type": "metric",
  "query": {
    "numerator": "sum:{service}.requests.success{env:{env}}.as_count()",
    "denominator": "sum:{service}.requests{env:{env}}.as_count()"
  },
  "thresholds": [
    { "timeframe": "30d", "target": 99.9, "warning": 99.95 }
  ],
  "tags": ["service:{service}", "env:{env}"]
}
```

Fast burn monitor (page) via `POST /api/v1/monitor`:

```json
{
  "name": "[{env}] {service} - SLO Fast Burn (14x / 1h)",
  "type": "slo alert",
  "query": "burn_rate(\"{slo_id}\").over(\"1h\").long_window(\"5h\").threshold(14)",
  "message": "**Fast SLO burn detected** for {service} in {env}.\nConsuming 30-day error budget at 14x rate — budget exhausted in ~2 days.\nRunbook: {runbook_url}\n@pagerduty-{team}",
  "tags": ["service:{service}", "env:{env}", "severity:page"]
}
```

Slow burn monitor (ticket) via `POST /api/v1/monitor`:

```json
{
  "name": "[{env}] {service} - SLO Slow Burn (5x / 6h)",
  "type": "slo alert",
  "query": "burn_rate(\"{slo_id}\").over(\"6h\").long_window(\"24h\").threshold(5)",
  "message": "**Slow SLO burn detected** for {service} in {env}.\nConsuming 30-day error budget at 5x rate — budget exhausted in ~6 days.\nRunbook: {runbook_url}\n@slack-{team}-alerts",
  "tags": ["service:{service}", "env:{env}", "severity:ticket"]
}
```

**Import methods:**
- **API:** `curl -X POST "https://api.datadoghq.com/api/v1/slo" -H "DD-API-KEY: $DD_API_KEY" -H "DD-APPLICATION-KEY: $DD_APP_KEY" -d @slo.json`
- **UI:** Dashboard gear icon → "Import Dashboard JSON" (for dashboards only; monitors/SLOs use the API)
- **datadog-sync-cli:** `datadog-sync import --resources="monitors,slos"` for bulk sync

---

## SLO Definition Worksheet

For each service, document:

```markdown
## SLO: [Service Name] — [SLI Type]

**SLI:** [What we measure — e.g., "% of HTTP requests returning non-5xx within 300ms"]

**SLO Target:** [e.g., 99.9%]

**SLO Window:** 30 days rolling

**Error Budget:** [e.g., 43.2 minutes per month]

**SLI Query (PromQL or Datadog):**
[Paste query here]

**Exclusions:**
- Health check endpoints (/livez, /readyz)
- [Any other excluded traffic]

**Burn Rate Thresholds:**
- Fast burn: 14x over 1h → page @on-call
- Slow burn: 5x over 6h → ticket in Jira

**Runbook:** [URL]

**Last Reviewed:** [date]
```

---

## Common Mistakes

| Mistake | Problem | Fix |
|---------|---------|-----|
| SLO window too short (7 days) | Error budget too small to act on | Use 28–30 day rolling window |
| Including health checks in SLI | Inflates request count, skews availability | Exclude in metric recording |
| 5xx only for errors | Misses timeouts (504 gateway timeout) and some 4xx (429 rate limit impacts) | Include 504, optionally 429 |
| Single burn rate window | Misses slow degradation or creates alert fatigue | Always use two windows |
| SLO tighter than reality | Constant error budget burn demotivates team | Start at P75 of historical availability |
| Not reviewing SLOs after incidents | SLO becomes disconnected from user experience | Quarterly review cadence |
