---
name: observability
description: "Instrument, audit, and configure observability for services using OpenTelemetry or Datadog. Detects which backend the project uses and routes to the appropriate specialist agent. Modes: instrument, audit, dashboard, alert, slo."
context: fork
allowed-tools: Bash, Read, Glob, Grep, Task
model: sonnet
tags: [observability]
---

# Observability

Instrument, audit, and configure observability for backend services. Detects your observability backend automatically and routes to the right specialist.

---

## Quick Start

```
/observability instrument        # Add instrumentation to this service
/observability audit             # Review current instrumentation coverage
/observability dashboard         # Generate Grafana/Datadog dashboard template
/observability alert             # Configure burn-rate alerts and monitors
/observability slo               # Define or review SLO targets and error budgets
```

**What to include in your request:**
- The mode (instrument, audit, dashboard, alert, slo)
- Target service name if different from current directory
- Any specific framework or language override if detection fails

---

## Triggers

| Trigger | Example |
|---------|---------|
| `instrument` | "add OpenTelemetry instrumentation to this service" |
| `add metrics` | "add RED metrics to the order service" |
| `add tracing` | "set up distributed tracing" |
| `observability audit` | "audit our current metrics coverage" |
| `SLO` | "set up SLOs for the payment service" |
| `error budget` | "calculate error budget for 99.9% SLO" |
| `dashboard` | "create a Grafana dashboard for this service" |
| `alert` | "configure burn-rate alerts" |
| `health check` | "add /livez and /readyz endpoints" |
| `structured logging` | "add trace correlation to our logs" |

---

## Key Terms

| Term | Definition |
|------|------------|
| **OTel / OpenTelemetry** | Vendor-neutral observability framework: traces, metrics, logs |
| **Datadog** | Commercial observability platform: APM, metrics, logs, monitors |
| **SLI** | Service Level Indicator — measurable proxy for user experience |
| **SLO** | Service Level Objective — target value for an SLI (e.g., 99.9% availability) |
| **Error Budget** | Allowable downtime/errors before SLO is breached |
| **RED Method** | Rate, Errors, Duration — metrics for microservices |
| **USE Method** | Utilization, Saturation, Errors — metrics for infrastructure |
| **Golden Signals** | Latency, Traffic, Errors, Saturation (Google SRE) |
| **Exemplar** | Trace ID attached to a histogram bucket linking metrics → traces |
| **Cardinality** | Number of unique time series; high cardinality = high cost |
| **Burn Rate** | How fast error budget is being consumed relative to SLO window |
| **Collector** | OTel Collector — agent that receives, processes, and exports telemetry |
| **DogStatsD** | Datadog's UDP metrics protocol |
| **Unified Service Tagging** | Datadog's `DD_ENV`, `DD_SERVICE`, `DD_VERSION` correlation tags |

---

## Detection: OTel vs Datadog

### Step 1: Scan Dependencies

DETECTED NODE DEPENDENCIES:
```
!`cat package.json 2>/dev/null | grep -E '"@opentelemetry|"dd-trace|"datadog-lambda|"@datadog' | head -20 || echo "package.json not found"`
```

DETECTED GO DEPENDENCIES:
```
!`cat go.mod 2>/dev/null | grep -E 'go.opentelemetry.io|datadog' | head -20 || echo "go.mod not found"`
```

DETECTED PYTHON DEPENDENCIES:
```
!`cat requirements.txt pyproject.toml 2>/dev/null | grep -E 'opentelemetry|ddtrace|datadog' | head -20 || echo "requirements.txt/pyproject.toml not found"`
```

DETECTED RUST DEPENDENCIES:
```
!`cat Cargo.toml 2>/dev/null | grep -E 'opentelemetry|datadog|axum-tracing' | head -20 || echo "Cargo.toml not found"`
```

DETECTED CONFIG FILES:
```
!`find . -maxdepth 4 \( -name "collector.yaml" -o -name "otel-collector.yaml" -o -name "otel-config.yaml" -o -name "datadog.yaml" \) 2>/dev/null | head -10 || echo "none"`
```

DETECTED DATADOG TERRAFORM:
```
!`grep -rl "datadog_monitor\|datadog_dashboard\|DD_API_KEY" . --include="*.tf" --include="*.hcl" 2>/dev/null | head -5 || echo "none"`
```

### Step 2: Interpret and Route

**OTel detected** if any of these appear in the scan output:
- Node: `@opentelemetry/`, `@opentelemetry/api`, `@opentelemetry/sdk-node`
- Go: `go.opentelemetry.io/otel`, `otelgin`, `otelchi`, `otelgrpc`
- Python: `opentelemetry-`, `opentelemetry-api`, `opentelemetry-sdk`
- Rust: `opentelemetry`, `axum-tracing-opentelemetry`, `tracing-opentelemetry`
- Config: `collector.yaml`, `otel-collector.yaml`, `otel-config.yaml`

**Datadog detected** if any of these appear in the scan output:
- Node: `dd-trace`, `datadog-lambda`, `@datadog/`
- Go: `gopkg.in/DataDog/dd-trace-go`
- Python: `ddtrace`, `datadog`
- Rust: `datadog` crate
- Config: `datadog.yaml`
- Terraform: `datadog_monitor`, `datadog_dashboard`, `DD_API_KEY`

**Routing rules:**

- **OTel only detected:** Invoke the `otel-instrumentation` agent via Task tool with the current mode and project context.
- **Datadog only detected:** Invoke the `datadog-instrumentation` agent via Task tool with the current mode and project context.
- **Both detected:** This is a valid architecture (OTel SDK → Datadog exporter). Ask the user: "I detected both OTel and Datadog dependencies. Are you using (1) OTel SDK with Datadog as the export backend, (2) native Datadog SDK, or (3) migrating between them?" Route based on answer.
- **Neither detected:** Ask the user: "I couldn't detect an observability backend. Are you using (1) OpenTelemetry/Prometheus, (2) Datadog, or (3) setting up from scratch?" Provide getting-started guidance for the chosen path before routing.

---

## Modes

| Mode | What It Does |
|------|-------------|
| `instrument` | Add SDK setup, auto-instrumentation, manual spans, structured logging, health endpoints |
| `audit` | Review existing instrumentation: coverage gaps, naming violations, cardinality risks, missing SLIs |
| `dashboard` | Generate Grafana (OTel) or Datadog dashboard template for the service (RED method + SLO panels) |
| `alert` | Configure burn-rate alerting rules (AlertManager for OTel, Datadog monitor JSON for Datadog) |
| `slo` | Define SLI queries, SLO targets, error budget calculation, and multi-window burn rate thresholds |

---

## Process Overview

```
User Request
    |
    v
+--------------------------------------------------+
| Phase 1: DETECT                                  |
| * Scan package.json / go.mod / requirements.txt |
| * Scan Cargo.toml / config files / Terraform     |
| * Determine OTel, Datadog, both, or neither      |
+--------------------------------------------------+
    |
    v
+--------------------------------------------------+
| Phase 2: CLARIFY (if ambiguous)                  |
| * Both detected: ask architecture intent         |
| * Neither detected: ask preferred backend        |
+--------------------------------------------------+
    |
    v
+--------------------------------------------------+
| Phase 3: ROUTE                                   |
| * OTel → otel-instrumentation agent              |
| * Datadog → datadog-instrumentation agent        |
+--------------------------------------------------+
    |
    v
+--------------------------------------------------+
| Phase 4: EXECUTE (in specialist agent)           |
| * Mode-specific work (instrument/audit/etc.)     |
| * Language and framework-specific guidance       |
| * Generate configs, code, dashboards             |
+--------------------------------------------------+
    |
    v
+--------------------------------------------------+
| Phase 5: VERIFY                                  |
| * Run verification checklist                     |
| * Confirm telemetry is emitting                  |
+--------------------------------------------------+
```

---

## Quick Reference

| Task | OTel Path | Datadog Path |
|------|-----------|-------------|
| Add traces | SDK auto-instrumentation | dd-trace SSI or SDK |
| Add metrics | OTel Meter API → Prometheus | DogStatsD or dd-trace |
| Add logs | SDK log bridge | DD log pipeline |
| Correlate logs+traces | `trace_id`/`span_id` (hex) | `dd.trace_id`/`dd.span_id` (decimal) |
| Health checks | `/livez` `/readyz` — exclude from traces | `/livez` `/readyz` — exclude from APM |
| Dashboard | Grafana (RED + SLO panels) | Datadog dashboard JSON (API import) |
| Alerts | AlertManager + PromQL | Datadog monitor JSON (`POST /api/v1/monitor`) |
| SLO tracking | PromQL recording rules | Datadog SLO JSON (`POST /api/v1/slo`) |

---

## Verification Checklist

After instrumentation work is complete:

- [ ] Service emits traces to collector/backend (verify with a test request)
- [ ] Traces show correct `service.name`, `deployment.environment`, `service.version`
- [ ] RED metrics are present: request rate, error rate, latency histogram
- [ ] Latency histogram uses correct base unit (`_seconds` for Prometheus, `ms` for Datadog)
- [ ] No unbounded cardinality labels (no user IDs, request IDs, raw URLs)
- [ ] Structured logs include `trace_id` and `span_id` in correct format
- [ ] `/livez` returns 200 (process alive check only)
- [ ] `/readyz` returns 200/503 based on dependency health
- [ ] Health endpoints are excluded from distributed tracing
- [ ] SLO target and error budget are documented
- [ ] At least one burn-rate alert is configured (fast-burn page, slow-burn ticket)
- [ ] Runbook URL is present in all alert messages

---

## References

- [references/metric-naming.md](references/metric-naming.md) — Prometheus and Datadog naming conventions
- [references/golden-signals.md](references/golden-signals.md) — RED/USE/Golden Signals with PromQL and Datadog queries
- [references/slo-calculator.md](references/slo-calculator.md) — SLO targets, error budgets, burn-rate formulas
- [references/structured-logging.md](references/structured-logging.md) — Required log fields, trace correlation by language
- [references/health-check-patterns.md](references/health-check-patterns.md) — /livez /readyz patterns, Kubernetes probes
- [references/framework-instrumentation.md](references/framework-instrumentation.md) — Quick-start code per language and framework
- [references/cardinality-guide.md](references/cardinality-guide.md) — Cardinality budgeting and anti-patterns
