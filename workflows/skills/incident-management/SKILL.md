---
name: incident-management
description: Cross-platform incident management router. Detects the alerting/on-call platform in use (Grafana IRM, incident.io, Better Stack, Datadog, PagerDuty) and routes to the appropriate specialist skill. Handles platform-agnostic tasks — alert design, on-call setup, runbook authoring, and blameless postmortems — without requiring platform knowledge.
context: fork
allowed-tools: Bash, Glob, Grep, Read, WebFetch
---

# Incident Management

Cross-platform incident management entry point. Detect the project's platform, then route to the appropriate specialist or execute a platform-agnostic task.

## When to Use

- Setting up alerting or on-call for a project without knowing which platform to use
- Designing alert rules, severity levels, or escalation policies
- Creating or improving runbooks
- Running a blameless postmortem
- Migrating from OpsGenie (shutting down April 2027) to a modern platform
- Getting guidance when the team is evaluating incident management platforms

## Platform Detection

Scan the repository to identify the active platform before routing:

```
!`grep -r "grafana_oncall\|grafana_irm\|grafana-irm" . --include="*.tf" --include="*.hcl" -l 2>/dev/null | head -5`
```

```
!`grep -r "incident\.io\|incidentio\|provider.*incident" . --include="*.tf" --include="*.hcl" -l 2>/dev/null | head -5`
```

```
!`grep -r "betterstack\|better_uptime\|better-stack" . --include="*.tf" --include="*.hcl" -l 2>/dev/null | head -5`
```

```
!`grep -r "pagerduty\|pagerduty_" . --include="*.tf" --include="*.hcl" -l 2>/dev/null | head -5`
```

```
!`grep -r "datadog_monitor\|DD_API_KEY\|datadoghq" . --include="*.tf" --include="*.hcl" --include="*.env*" -l 2>/dev/null | head -5`
```

## Routing Logic

| Platform Detected | Route To |
|---|---|
| `grafana_oncall_*` or `grafana_irm_*` in Terraform | `/grafana-irm` specialist |
| `provider "incident"` or `incidentio_*` in Terraform | `/incident-io` specialist |
| `betterstack_*` or `better_uptime_*` in Terraform | `/better-stack` specialist |
| `pagerduty_*` in Terraform | `/pagerduty` specialist (if available) or generic guidance |
| `datadog_monitor` or `DD_API_KEY` | `/observability` skill with `incident` mode |
| No platform detected | Present evaluation matrix below, ask user to confirm |

## Platform-Agnostic Modes

When invoked without a detected platform, or explicitly for cross-cutting concerns:

### `design-alerts`
Design symptom-based alert rules from scratch. Use `references/alerting-patterns.md` and `references/severity-taxonomy.md`.

Gather:
1. Service name and language/framework
2. Key user-visible operations (checkout, login, search, etc.)
3. Current p50/p75/p99 latency baselines (if known)
4. Existing monitoring stack (Prometheus, Datadog, Grafana, etc.)

Output: severity-classified alert definitions with thresholds, burn-rate windows, and runbook URLs.

### `on-call-setup`
Design an on-call rotation structure. Use `references/on-call-rotation.md`.

Gather:
1. Number of engineers available for rotation
2. Team timezone distribution
3. Current shift length preference
4. Whether a shadow/mentorship rotation is needed

Output: rotation schedule template, escalation policy tiers, handoff checklist.

### `runbook`
Create or improve an alert runbook. Use `references/runbook-template.md`.

Gather:
1. Alert name and firing condition
2. Service affected and owner team
3. Known common causes
4. Existing remediation steps (if any)

Output: complete runbook following the standard six-section structure.

### `postmortem`
Facilitate a blameless postmortem. Use `references/postmortem-template.md`.

Gather:
1. Incident timeline (start, detection, triage, resolution)
2. SEV level and user impact
3. Immediate contributing factors
4. Systems and people involved

Output: completed postmortem document with action items.

### `evaluate`
Platform evaluation for teams choosing between Grafana IRM, incident.io, Better Stack, and PagerDuty.

Present the comparison matrix from `references/alerting-patterns.md` and guide through:
1. Existing stack compatibility (Grafana, OTel, Slack, Datadog)
2. MCP integration requirements
3. Terraform workflow maturity
4. Budget and seat count constraints

## Platform Status Warnings

Surface these when relevant:

- **OpsGenie:** New sales ended June 2025; full shutdown April 5, 2027. Recommend migration to Grafana IRM, incident.io, or Better Stack.
- **Grafana OnCall OSS:** Maintenance mode March 2025; archived March 2026. Route all OSS OnCall users to Grafana Cloud IRM.
- **FireHydrant:** Acquired by Freshworks 2025. Avoid new skill investment.
- **Squadcast:** Acquired by SolarWinds 2025. Avoid new skill investment.

## References

- `references/alerting-patterns.md` — Platform-agnostic alert design, SLO burn rate, fatigue mitigation
- `references/severity-taxonomy.md` — SEV0–SEV3 definitions, escalation policy tiers
- `references/on-call-rotation.md` — Rotation patterns, handoff templates, follow-the-sun
- `references/runbook-template.md` — Standard runbook structure
- `references/postmortem-template.md` — Blameless postmortem structure and facilitation guide
