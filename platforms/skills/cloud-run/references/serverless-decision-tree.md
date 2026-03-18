# Serverless Decision Tree: Cloud Run vs Cloud Functions vs GKE

## Primary Decision Tree

```
Do you need to manage your own container image?
  Yes → Cloud Run (Services or Jobs)
  No  → Cloud Functions 2nd gen (abstracts container concerns)

Is your workload request-driven (HTTP, gRPC)?
  Yes → Cloud Run Services
  No, it's event-driven → Cloud Functions 2nd gen or Cloud Run + Eventarc

Does the workload run to completion (not a long-running server)?
  Yes → Cloud Run Jobs (batch) or Cloud Functions (short tasks)
  No  → Cloud Run Services

Does the workload need:
  - Multi-container pods? → GKE
  - GPU/accelerator access? → Cloud Run (GPU support added 2024) or GKE
  - Execution > 60 minutes? → Cloud Run Jobs (24h limit) or GKE
  - Stateful workloads (e.g., databases)? → GKE with StatefulSets
  - Existing Kubernetes ecosystem? → GKE
```

## Detailed Comparison

| Dimension | Cloud Run Services | Cloud Run Jobs | Cloud Functions 2nd gen | GKE |
|-----------|-------------------|----------------|------------------------|-----|
| **Request model** | HTTP/gRPC (long-polling OK) | Run to completion | HTTP or event-triggered | Any |
| **Max execution time** | 60 minutes per request | 24 hours per task | 60 minutes | Unlimited |
| **Concurrency** | Up to 1000 per instance | 1 per task | 1 per instance (default) | Up to pod limits |
| **Scaling** | 0 → 1000 instances automatically | 0 → 10,000 tasks | 0 → 3000 instances | Manual + HPA + Karpenter |
| **Container control** | Full container control | Full container control | Source-based (no Dockerfile needed) | Full pod control |
| **Multi-container** | Sidecars (via YAML only) | No | No | Yes (full pod spec) |
| **VPC access** | Serverless VPC Access connector | Serverless VPC Access connector | Serverless VPC Access connector | Native VPC |
| **GPU support** | Yes (NVIDIA L4, T4) | No | No | Yes (full GPU support) |
| **Cold start** | ~100–500ms (JVM: ~2–5s) | Not applicable | ~100ms–2s | Minimal (pods pre-warm) |
| **Cost model** | Per-request or CPU-always | Per task execution | Per request | Node pool (always-on) |
| **Minimum expertise** | Low (just push an image) | Low | Very low (just write a function) | High (Kubernetes) |

## Cloud Run Services: Best For

- REST APIs and gRPC services
- Backend services with variable traffic (0 → spike → 0)
- Containerized applications migrated from VMs
- Services that need VPC egress (Cloud SQL, Memorystore) via connector
- Services with consistent load that benefit from min-instances

## Cloud Run Jobs: Best For

- Scheduled batch processing (via Cloud Scheduler)
- Database migrations (run-once tasks)
- Data export/import pipelines
- Parallel task processing across shards (`CLOUD_RUN_TASK_INDEX`)
- One-off operational tasks (e.g., "rebuild all search indexes")

## Cloud Functions 2nd gen: Best For

- Event-driven handlers with minimal setup (no Dockerfile needed)
- Reacting to GCS events, Pub/Sub messages, Firestore changes, Eventarc triggers
- Simple HTTP functions without container overhead
- Teams that prefer function-as-unit-of-deployment over service-as-unit

**Note:** 2nd gen functions deploy as Cloud Run services under the hood. They share the same scaling model, the same networking options (VPC connector), and the same IAM patterns. Choose based on developer experience preference.

## GKE: Best For

- Teams with existing Kubernetes expertise and tooling
- Workloads needing multi-container pods (sidecar-heavy architectures)
- Stateful workloads with persistent volumes
- Long-running processes (daemons, queue workers with no time limit)
- GPU inference at scale
- Strict node-level control (node affinity, taints, specific machine types)

## Cost Guidance

| Traffic Pattern | Cloud Run | GKE |
|-----------------|-----------|-----|
| Intermittent (spiky) | Lower — scales to 0 | Higher — minimum node pool |
| Consistent high throughput | Comparable | Comparable (may be lower at scale) |
| Always-on, max instances | Add baseline cost for min-instances | GKE node pool cost is predictable |

For new backend services with variable traffic: **Cloud Run is the default choice**. GKE is the choice when Kubernetes-specific capabilities are required.
