# Alerting Patterns (Platform-Agnostic)

Cross-platform alerting best practices. These principles apply regardless of whether you're configuring Grafana IRM, incident.io, Better Stack, Datadog, or PagerDuty. For platform-specific Terraform and MCP usage, see the specialist skill for your platform.

**Related references:**
- OTel/Prometheus SLO burn-rate rules: `../../../observability/references/slo-calculator.md`
- Golden signals baseline: `../../../observability/references/golden-signals.md`

---

## Alert Design Principles

### Symptom-Based, Not Cause-Based

Page on user-visible impact. Never page on infrastructure internals.

**Page on (symptoms):**
- Error rate > threshold
- P95/P99 latency > threshold
- Availability < SLO target (burn-rate alert)
- Service completely unreachable

**Never page on (causes):**
- CPU > 80%
- Memory > 75%
- Pod restart count
- GC pause duration
- Disk usage < 95%
- Queue depth (unless tied to latency SLO)

### Every Alert Must Have

| Field | Requirement |
|---|---|
| Actionable response | If a robot can handle it, a human should not be paged |
| Urgency | Every page must feel urgent; fatigue kills this |
| Runbook URL | Link to the specific procedure, not a general wiki |
| Context | Current value, threshold, impact estimate, dashboard link |
| Owner | Which team or rotation receives the notification |

### Alert Message Anatomy

```
[SEV1] order-service: Error Rate Elevated (production)
- Current: 3.2%  |  Threshold: 1%
- Impact: ~320 req/min failing
- Duration: 4m 30s
- Runbook: https://wiki.example.com/runbooks/order-service-errors
- Dashboard: https://grafana.example.com/d/order-service
- Trace sample: <link to trace>
@oncall-platform
```

---

## SLO-Based Alerting (Multi-Window Burn Rate)

The gold standard. Alerts on error budget consumption rate rather than raw error count.

### Fast Burn (Page Now)
```
Short window: 1h at 14x burn rate
Long window:  5h at 14x burn rate  (confirmation guard)
Action:       Wake on-call, start incident bridge
```

At 14x burn rate with a 30-day SLO window, the budget exhausts in ~2 days.

### Slow Burn (Create Ticket)
```
Short window: 6h at 5x burn rate
Long window:  3d at 5x burn rate
Action:       Create Jira/Linear ticket, review in sprint planning
```

### PromQL Example (Prometheus / Grafana)
```promql
# Fast burn: error rate > 14x expected
(
  rate(http_requests_total{status=~"5.."}[1h])
  /
  rate(http_requests_total[1h])
) > (14 * (1 - 0.999))

AND

(
  rate(http_requests_total{status=~"5.."}[5h])
  /
  rate(http_requests_total[5h])
) > (14 * (1 - 0.999))
```

### SLO Starting Points

- Use P75 of historical performance as the SLO baseline target
- Do not set targets tighter than you have achieved in the past 90 days
- Tighten SLOs after two consecutive clean quarters, not as aspirational targets

---

## Alert Fatigue Mitigation

### Monthly Review Rule

Any alert firing more than 5x per week without triggering a remediation action is a noise alert. It must be:
1. Tuned (threshold too low)
2. Automated (remediation can run without human)
3. Eliminated (not actionable by definition)

### Grouping and Deduplication

One incident per outage, not one page per symptom. Group correlated alerts:
- Same service + same time window → single incident
- Related services in dependency chain → parent incident with children

### Inhibition Rules

Suppress low-severity alerts when a high-severity alert is active for the same service or dependency:
- SEV2 alerts inhibited during active SEV0/SEV1 for the same service
- Dependency-downstream alerts inhibited when the upstream service is paging

### Maintenance Windows

- Always pre-schedule silence windows before deployments or maintenance
- Never ad-hoc silence during active fire-fighting (masks real issues)
- Duration: set to 2x expected maintenance window to absorb delays

---

## Platform Comparison Matrix (Current as of 2025)

| Platform | Alert Routing | On-Call Scheduling | Terraform Provider | MCP Server | Status Pages | Postmortem Tooling |
|---|---|---|---|---|---|---|
| **Grafana IRM** (Cloud) | Yes — integrations + escalation chains | Yes — schedules, rotations | Yes — `grafana` provider, `grafana_oncall_*` | Yes — `grafana/mcp-grafana` (official) | No native | Basic |
| **incident.io** | Yes — alert routing, workflows | Yes | Yes — official provider v5+ | Yes — official, Claude-native | Via partner | Yes — structured retros |
| **Better Stack** | Yes — monitors → on-call | Yes — policies, rotations | Yes — `BetterStackHQ/better-uptime` | Yes — official MCP | Yes — branded, custom domain | AI-assisted drafts |
| **Datadog Incidents** | Yes — via DD monitors | No native (PagerDuty integration) | Yes — `datadog` provider | Yes — official remote MCP (preview) | No | Yes — timeline auto-generated |
| **PagerDuty** | Yes | Yes — schedules, rotations | Yes — `pagerduty` provider | Yes — official MCP server | Yes | Yes — postmortem builder |

### Selection Heuristics

| Situation | Recommendation |
|---|---|
| Already on Grafana + OTel/Prometheus | Grafana IRM — zero new vendor, seamless integration |
| Slack-native team, modern SRE shop | incident.io — best-in-class Slack UX, fastest onboarding |
| Startup wanting consolidated monitoring + alerting + status pages | Better Stack — best value, bundles everything |
| Already fully on Datadog | Datadog Incidents — consolidate, no new vendor |
| Migrating from OpsGenie (deadline: April 2027) | Evaluate incident.io or Grafana IRM first |
| Large enterprise with existing PagerDuty contract | PagerDuty — switching cost likely outweighs gains |
