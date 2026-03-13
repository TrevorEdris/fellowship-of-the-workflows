# Framework Instrumentation Quick-Start

Quick-start code for instrumenting common frameworks with both OTel and Datadog paths.

---

## Go — Gin

### OTel Path

```bash
go get go.opentelemetry.io/otel \
       go.opentelemetry.io/otel/sdk \
       go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracegrpc \
       go.opentelemetry.io/otel/exporters/prometheus \
       go.opentelemetry.io/contrib/instrumentation/github.com/gin-gonic/gin/otelgin
```

```go
// main.go
package main

import (
    "context"
    "log"
    "net/http"
    "os"

    "github.com/gin-gonic/gin"
    "go.opentelemetry.io/contrib/instrumentation/github.com/gin-gonic/gin/otelgin"
    "go.opentelemetry.io/otel"
    "go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracegrpc"
    "go.opentelemetry.io/otel/exporters/prometheus"
    "go.opentelemetry.io/otel/propagation"
    "go.opentelemetry.io/otel/sdk/metric"
    "go.opentelemetry.io/otel/sdk/resource"
    sdktrace "go.opentelemetry.io/otel/sdk/trace"
    semconv "go.opentelemetry.io/otel/semconv/v1.26.0"
    "github.com/prometheus/client_golang/prometheus/promhttp"
)

func initOTel(ctx context.Context) func() {
    res, _ := resource.New(ctx,
        resource.WithAttributes(
            semconv.ServiceName(os.Getenv("OTEL_SERVICE_NAME")),
            semconv.ServiceVersion(os.Getenv("SERVICE_VERSION")),
            semconv.DeploymentEnvironment(os.Getenv("DEPLOY_ENV")),
        ),
    )

    traceExporter, _ := otlptracegrpc.New(ctx)
    tp := sdktrace.NewTracerProvider(
        sdktrace.WithBatcher(traceExporter),
        sdktrace.WithResource(res),
    )
    otel.SetTracerProvider(tp)
    otel.SetTextMapPropagator(propagation.NewCompositeTextMapPropagator(
        propagation.TraceContext{},
        propagation.Baggage{},
    ))

    promExporter, _ := prometheus.New()
    mp := metric.NewMeterProvider(metric.WithReader(promExporter), metric.WithResource(res))
    otel.SetMeterProvider(mp)

    return func() {
        tp.Shutdown(ctx)
        mp.Shutdown(ctx)
    }
}

func main() {
    ctx := context.Background()
    shutdown := initOTel(ctx)
    defer shutdown()

    r := gin.New()
    r.Use(gin.Recovery())
    r.Use(otelgin.Middleware(os.Getenv("OTEL_SERVICE_NAME")))

    // Health checks — registered before OTel middleware takes effect
    r.GET("/livez", func(c *gin.Context) { c.JSON(http.StatusOK, gin.H{"status": "ok"}) })
    r.GET("/readyz", readyzHandler)

    // Prometheus metrics
    r.GET("/metrics", gin.WrapH(promhttp.Handler()))

    r.POST("/orders", createOrderHandler)
    r.Run(":8080")
}
```

### Datadog Path (Gin)

```bash
go get gopkg.in/DataDog/dd-trace-go.v1/ddtrace/tracer \
       gopkg.in/DataDog/dd-trace-go.v1/contrib/gin-gonic/gin
```

```go
package main

import (
    "github.com/gin-gonic/gin"
    gintrace "gopkg.in/DataDog/dd-trace-go.v1/contrib/gin-gonic/gin"
    "gopkg.in/DataDog/dd-trace-go.v1/ddtrace/tracer"
    "os"
)

func main() {
    tracer.Start(
        tracer.WithService(os.Getenv("DD_SERVICE")),
        tracer.WithEnv(os.Getenv("DD_ENV")),
        tracer.WithServiceVersion(os.Getenv("DD_VERSION")),
        tracer.WithRuntimeMetrics(),
    )
    defer tracer.Stop()

    r := gin.New()
    r.Use(gin.Recovery())
    r.Use(gintrace.Middleware(os.Getenv("DD_SERVICE")))

    r.GET("/livez", func(c *gin.Context) { c.JSON(200, gin.H{"status": "ok"}) })
    r.GET("/readyz", readyzHandler)
    r.POST("/orders", createOrderHandler)
    r.Run(":8080")
}
```

---

## Go — Chi

### OTel Path

```bash
go get go.opentelemetry.io/contrib/instrumentation/net/http/otelhttp
```

```go
import (
    "go.opentelemetry.io/contrib/instrumentation/net/http/otelhttp"
    "github.com/go-chi/chi/v5"
)

r := chi.NewRouter()
r.Use(func(next http.Handler) http.Handler {
    return otelhttp.NewHandler(next, "",
        otelhttp.WithSpanNameFormatter(func(op string, r *http.Request) string {
            // Use chi route template for span name
            rctx := chi.RouteContext(r.Context())
            if rctx != nil && rctx.RoutePattern() != "" {
                return r.Method + " " + rctx.RoutePattern()
            }
            return r.Method + " " + r.URL.Path
        }),
    )
})
```

### Datadog Path (Chi)

```bash
go get gopkg.in/DataDog/dd-trace-go.v1/contrib/go-chi/chi.v5
```

```go
import chitrace "gopkg.in/DataDog/dd-trace-go.v1/contrib/go-chi/chi.v5"

r := chi.NewRouter()
r.Use(chitrace.Middleware(chitrace.WithServiceName(os.Getenv("DD_SERVICE"))))
```

---

## Node.js — Express

### OTel Path

```bash
npm install @opentelemetry/sdk-node @opentelemetry/auto-instrumentations-node \
  @opentelemetry/exporter-trace-otlp-grpc @opentelemetry/exporter-prometheus
```

```javascript
// instrumentation.js — MUST be required first
const { NodeSDK } = require('@opentelemetry/sdk-node');
const { getNodeAutoInstrumentations } = require('@opentelemetry/auto-instrumentations-node');
const { OTLPTraceExporter } = require('@opentelemetry/exporter-trace-otlp-grpc');
const { PrometheusExporter } = require('@opentelemetry/exporter-prometheus');
const { Resource } = require('@opentelemetry/resources');
const { ATTR_SERVICE_NAME, ATTR_SERVICE_VERSION } = require('@opentelemetry/semantic-conventions');

const sdk = new NodeSDK({
  resource: new Resource({
    [ATTR_SERVICE_NAME]: process.env.OTEL_SERVICE_NAME || 'order-service',
    [ATTR_SERVICE_VERSION]: process.env.SERVICE_VERSION || '0.0.0',
  }),
  traceExporter: new OTLPTraceExporter(),
  metricReader: new PrometheusExporter({ port: 9464 }),
  instrumentations: [getNodeAutoInstrumentations({
    '@opentelemetry/instrumentation-http': {
      ignoreIncomingRequestHook: (req) =>
        req.url === '/livez' || req.url === '/readyz',
    },
  })],
});

sdk.start();
process.on('SIGTERM', () => sdk.shutdown());
```

```javascript
// app.js
// node --require ./instrumentation.js app.js
const express = require('express');
const app = express();
app.use(express.json());

app.get('/livez', (req, res) => res.json({ status: 'ok' }));
app.get('/readyz', readyzHandler);
app.post('/orders', createOrderHandler);
app.listen(8080);
```

### Datadog Path (Express)

```bash
npm install dd-trace
```

```javascript
// Must be first line
const tracer = require('dd-trace').init({
  service: process.env.DD_SERVICE || 'order-service',
  env: process.env.DD_ENV || 'production',
  version: process.env.DD_VERSION || '0.0.0',
  logInjection: true,
  runtimeMetrics: true,
  // Exclude health endpoints from APM traces
  blocklist: ['/livez', '/readyz'],
});

const express = require('express');
const app = express();
app.use(express.json());

app.get('/livez', (req, res) => res.json({ status: 'ok' }));
app.get('/readyz', readyzHandler);
app.post('/orders', createOrderHandler);
app.listen(8080);
```

---

## Node.js — Fastify

### OTel Path

```bash
npm install @opentelemetry/sdk-node @opentelemetry/auto-instrumentations-node \
  @opentelemetry/instrumentation-fastify
```

```javascript
// Same instrumentation.js as Express (auto-instrumentation covers Fastify)
// fastify-specific: add @opentelemetry/instrumentation-fastify to instrumentations array
const { FastifyInstrumentation } = require('@opentelemetry/instrumentation-fastify');

// In NodeSDK:
instrumentations: [
  getNodeAutoInstrumentations(),
  new FastifyInstrumentation(),
],
```

### Datadog Path (Fastify)

```javascript
// dd-trace auto-instruments Fastify — same init as Express
const tracer = require('dd-trace').init({
  service: process.env.DD_SERVICE,
  env: process.env.DD_ENV,
  logInjection: true,
});

const fastify = require('fastify')({ logger: true });
fastify.get('/livez', async () => ({ status: 'ok' }));
fastify.get('/readyz', readyzHandler);
fastify.post('/orders', createOrderHandler);
fastify.listen({ port: 8080 });
```

---

## Python — FastAPI

### OTel Path

```bash
pip install opentelemetry-sdk opentelemetry-exporter-otlp-proto-grpc \
  opentelemetry-instrumentation-fastapi opentelemetry-instrumentation-sqlalchemy \
  opentelemetry-instrumentation-httpx opentelemetry-exporter-prometheus
```

```python
# main.py
import os
from fastapi import FastAPI
from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.exporter.prometheus import PrometheusMetricReader
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import Resource, SERVICE_NAME, SERVICE_VERSION
from prometheus_client import make_asgi_app

resource = Resource({
    SERVICE_NAME: os.environ["OTEL_SERVICE_NAME"],
    SERVICE_VERSION: os.environ.get("SERVICE_VERSION", "0.0.0"),
})

tracer_provider = TracerProvider(resource=resource)
tracer_provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
trace.set_tracer_provider(tracer_provider)

meter_provider = MeterProvider(
    resource=resource,
    metric_readers=[PrometheusMetricReader()]
)
metrics.set_meter_provider(meter_provider)

app = FastAPI()

# Exclude health endpoints from instrumentation
FastAPIInstrumentor.instrument_app(
    app,
    excluded_urls="livez,readyz",
)

# Mount Prometheus metrics
app.mount("/metrics", make_asgi_app())

@app.get("/livez")
async def livez():
    return {"status": "ok"}

@app.get("/readyz")
async def readyz():
    # dependency checks
    return {"status": "ok"}
```

### Datadog Path (FastAPI)

```bash
pip install ddtrace
```

```bash
# Zero-code auto-instrumentation:
DD_SERVICE=order-service DD_ENV=production DD_VERSION=1.0.0 ddtrace-run uvicorn main:app
```

```python
# For custom spans within FastAPI:
from ddtrace import tracer

@app.post("/orders")
async def create_order(order: OrderRequest):
    with tracer.trace("validate_order", service=os.environ["DD_SERVICE"]) as span:
        span.set_tag("order.amount", order.amount)
        validate(order)
    # APM auto-instruments the HTTP layer
    result = await process_order(order)
    return result
```

---

## Python — Django

### OTel Path

```bash
pip install opentelemetry-instrumentation-django opentelemetry-exporter-otlp-proto-grpc
```

```python
# settings.py
INSTALLED_APPS = [
    # ... existing apps
]

# Initialize OTel before Django starts (in manage.py or wsgi.py)
# manage.py:
import os
from opentelemetry.instrumentation.django import DjangoInstrumentor

DjangoInstrumentor().instrument(
    excluded_urls="livez,readyz",
)
```

### Datadog Path (Django)

```bash
pip install ddtrace
```

```bash
# management command:
DD_SERVICE=my-django-app ddtrace-run python manage.py runserver

# gunicorn:
DD_SERVICE=my-django-app ddtrace-run gunicorn myapp.wsgi
```

---

## Rust — Axum

### OTel Path

```toml
# Cargo.toml
[dependencies]
axum = "0.7"
axum-tracing-opentelemetry = "0.21"
opentelemetry = { version = "0.23", features = ["trace"] }
opentelemetry-otlp = { version = "0.16", features = ["grpc-tonic"] }
opentelemetry_sdk = { version = "0.23", features = ["rt-tokio"] }
tracing = "0.1"
tracing-opentelemetry = "0.24"
tracing-subscriber = { version = "0.3", features = ["env-filter", "json"] }
```

```rust
use axum::{routing::get, Router};
use axum_tracing_opentelemetry::middleware::{OtelAxumLayer, OtelInResponseLayer};
use opentelemetry_otlp::WithExportConfig;
use tracing_subscriber::{layer::SubscriberExt, util::SubscriberInitExt};

fn init_tracer() {
    opentelemetry_otlp::new_pipeline()
        .tracing()
        .with_exporter(
            opentelemetry_otlp::new_exporter()
                .tonic()
                .with_endpoint(std::env::var("OTEL_EXPORTER_OTLP_ENDPOINT").unwrap()),
        )
        .install_batch(opentelemetry_sdk::runtime::Tokio)
        .expect("Failed to initialize OTel tracer");

    tracing_subscriber::registry()
        .with(tracing_subscriber::EnvFilter::from_default_env())
        .with(tracing_subscriber::fmt::layer().json())
        .with(tracing_opentelemetry::layer())
        .init();
}

#[tokio::main]
async fn main() {
    init_tracer();

    // Health routes registered BEFORE OTel middleware
    let app = Router::new()
        .route("/livez", get(livez))
        .route("/readyz", get(readyz))
        .layer(OtelInResponseLayer)
        .layer(OtelAxumLayer::default())
        .route("/orders", axum::routing::post(create_order));

    axum::serve(
        tokio::net::TcpListener::bind("0.0.0.0:8080").await.unwrap(),
        app,
    ).await.unwrap();
}

async fn livez() -> axum::Json<serde_json::Value> {
    axum::Json(serde_json::json!({"status": "ok"}))
}
```

### Datadog Path (Axum)

Datadog does not have an official Rust SDK with Axum middleware. Options:

1. **OTel SDK → Datadog exporter** (recommended): Use OTel setup above with `opentelemetry-datadog` crate as the exporter backend.

```toml
[dependencies]
opentelemetry-datadog = { version = "0.11", features = ["reqwest-client"] }
```

```rust
opentelemetry_datadog::new_pipeline()
    .with_service_name(std::env::var("DD_SERVICE").unwrap())
    .with_agent_endpoint("http://localhost:8126")
    .install_batch(opentelemetry_sdk::runtime::Tokio)
    .expect("Failed to initialize Datadog exporter");
```

2. **DogStatsD custom metrics** (for custom counters/gauges alongside OTel traces):

```bash
cargo add dogstatsd
```

```rust
use dogstatsd::{Client, Options};

let client = Client::new(Options::default()).unwrap();
client.incr("order.service.requests", &["env:production", "service:order-service"]).unwrap();
client.distribution("order.service.duration", 235.0, &["env:production"]).unwrap();
```

---

## Rust — Actix-web

### OTel Path

```toml
[dependencies]
actix-web = "4"
tracing-actix-web = "0.7"
opentelemetry-otlp = { version = "0.16", features = ["grpc-tonic"] }
opentelemetry_sdk = { version = "0.23", features = ["rt-tokio"] }
tracing-opentelemetry = "0.24"
tracing-subscriber = { version = "0.3", features = ["json"] }
```

```rust
use actix_web::{web, App, HttpServer};
use tracing_actix_web::TracingLogger;

#[actix_web::main]
async fn main() -> std::io::Result<()> {
    init_tracer(); // same as Axum OTel setup

    HttpServer::new(|| {
        App::new()
            .wrap(TracingLogger::default())
            .route("/livez", web::get().to(livez))
            .route("/readyz", web::get().to(readyz))
            .route("/orders", web::post().to(create_order))
    })
    .bind("0.0.0.0:8080")?
    .run()
    .await
}
```

---

## Environment Variables Summary

| Variable | OTel | Datadog | Purpose |
|----------|------|---------|---------|
| Service name | `OTEL_SERVICE_NAME` | `DD_SERVICE` | Identify the service |
| Environment | `OTEL_RESOURCE_ATTRIBUTES=deployment.environment=prod` | `DD_ENV` | Deployment environment |
| Version | `OTEL_RESOURCE_ATTRIBUTES=service.version=1.0.0` | `DD_VERSION` | Deployed version |
| Export endpoint | `OTEL_EXPORTER_OTLP_ENDPOINT` | `DD_AGENT_HOST` + port 8126 | Where to send telemetry |
| Sampling | `OTEL_TRACES_SAMPLER=parentbased_traceidratio` + `OTEL_TRACES_SAMPLER_ARG=0.1` | `DD_TRACE_SAMPLE_RATE=0.1` | Sampling rate |
| Log level | `OTEL_LOG_LEVEL=info` | `DD_TRACE_DEBUG=false` | SDK verbosity |
