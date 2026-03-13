---
name: pagerduty
description: "Configure PagerDuty services, escalation policies, on-call schedules, event routing, and IaC. Modes: setup, routing, incidents, terraform."
context: fork
agent: pagerduty-config
allowed-tools: Bash, Read, Glob, Grep, Task
model: sonnet
---

# PagerDuty

Configure the PagerDuty notification and escalation layer. PagerDuty sits downstream of your monitoring stack (AlertManager, Datadog, Grafana) — it is responsible for who gets paged, when, and how. This skill does not define SLOs or alerting rules; it configures the PD side that receives those alerts.

## When to Use

- Setting up a new PD service, escalation policy, or on-call schedule
- Configuring event routing, deduplication, or suppression rules
- Integrating Datadog, AlertManager, or Grafana with PagerDuty
- Generating or auditing Terraform for PD resources
- Managing incident workflows, priority tiers, or postmortem automation
- Reducing alert fatigue by tuning severity mapping and noise tiering

## Modes

```
/pagerduty setup       # Create PD services, escalation policies, on-call schedules
/pagerduty routing     # Configure event orchestration rules, severity mapping, dedup_key design
/pagerduty incidents   # Incident workflows, postmortem automation, priority tiers
/pagerduty terraform   # Generate/audit IaC for PD resources using the pagerduty provider
```

**Default behavior (no argument):** Scan for `pagerduty_service` Terraform resources in the current project. If found, default to `terraform` mode. If not found, default to `setup` mode.

## Context

Detected Terraform PagerDuty resources:

```
!`grep -rl "pagerduty_service\|pagerduty_escalation_policy\|pagerduty_schedule" . --include="*.tf" 2>/dev/null | head -20 || echo "No PagerDuty Terraform resources found"`
```

Detected AlertManager configs:

```
!`find . -name "alertmanager*.yaml" -o -name "alertmanager*.yml" 2>/dev/null | head -10 || echo "No AlertManager configs found"`
```

## Mode: setup

Design and implement PD services, escalation policies, and on-call schedules.

1. Identify the team and service boundaries (one PD service per logical concern, not per deployment unit).
2. Design an escalation policy following the standard three-level structure:
   - L1: On-call engineer — 5-minute acknowledge timeout
   - L2: Team lead — 15-minute timeout
   - L3: Manager — 30-minute timeout
3. Design on-call schedules with weekly rotation layers, primary and secondary (shadow) coverage, and handoff time.
4. Validate schedule coverage: no gaps > 15 minutes, at least 2 reachable people, no single person on rotation > 5 consecutive days.
5. Configure `auto_resolve_timeout` per criticality tier: critical = no auto-resolve, high = 4h (14400s), medium = 2h (7200s).
6. Configure alert grouping: time-based grouping (5-minute window) to suppress duplicate pages from the same service.

Reference: `references/escalation-policy-design.md`

## Mode: routing

Configure how events flow into PagerDuty and how they are deduplicated and suppressed.

1. Design `dedup_key` values using the `{service}:{alert_rule}:{env}` pattern.
2. Map source tool severity to PD severity — never route `info` events to PD.
3. Configure event orchestration rules (global or service-level) as a DAG evaluated top-down.
4. Set suppression windows via `POST /maintenance_windows` for planned maintenance.
5. Apply flapping suppression: require `for: 2m` in AlertManager before routing to PD.
6. Tier all alerts into three categories: page (P1/P2 incident), notify (Slack + low-urgency PD), log (monitoring tool only).

Reference: `references/events-api-v2.md`, `references/severity-mapping.md`, `references/noise-reduction.md`

## Mode: incidents

Configure incident lifecycle, response automation, and postmortem workflows.

1. Define priority tiers: P1 (critical, business impact, all-hands), P2 (high, on-call response), P3 (medium, next-day), P4 (low, backlog).
2. Configure incident workflows (triggered at open/acknowledge/resolve) to post to Slack, create Jira tickets, or run webhooks.
3. Set up subscriber notifications for stakeholders on high-severity services (does not page them).
4. Configure postmortem automation: PD generates a template from the incident timeline; integrate with Confluence or Notion via webhook.
5. For runbook automation: PD incident webhooks can trigger Lambda, Cloud Functions, or Argo Workflows for automated remediation.

Reference: `references/incident-management.md`

## Mode: terraform

Generate or audit Terraform for PD resources using the `hashicorp/pagerduty` provider (v3.x).

1. Scan existing `.tf` files for PD resources and identify what is managed vs. manually created.
2. For manually created resources: generate `terraform import` commands (service IDs are in the PD UI URL).
3. Generate a reusable module using the template in `assets/terraform-module/`.
4. The module outputs `integration_key` — this is the handoff to your observability Terraform (Datadog monitors, AlertManager configs).
5. Audit for convention violations: hardcoded `routing_key` values, missing `dedup_key`, incorrect severity mapping.

Reference: `references/terraform-patterns.md`

## Layer Model

```
[Monitoring Tool]         Detection Layer
AlertManager / Datadog    Generates signals: error rate, burn rate, latency
                                |
                                | routes events via integration key
                                v
[PagerDuty]               Notification / Escalation Layer
                          Owns: schedules, escalation policies, dedup, suppression
                                |
                                | pages
                                v
[On-Call Engineer]        Response Layer
```

The `integration_key` (output of `pagerduty_service_integration`) is the contract between the two layers. Your observability Terraform consumes this key.

## Security Conventions

- Never hardcode `routing_key` (Events API integration key) in HCL or source code — store in Vault or as a Kubernetes secret.
- Use a dedicated API token per automation context, not a shared account token.
- Read-only tokens for lookup operations; write tokens for incident management automation.
- Verify `X-PagerDuty-Signature` (HMAC-SHA256) on all incoming PD webhooks before processing.
- Enable IP allowlisting at the account level for automation tokens.

## References

- `references/events-api-v2.md` — Events API v2 payload format, dedup_key lifecycle
- `references/escalation-policy-design.md` — Policy structure, level limits, schedule validation
- `references/terraform-patterns.md` — Provider resources, reusable module, import guide
- `references/severity-mapping.md` — AlertManager/Datadog severity → PD severity mapping
- `references/noise-reduction.md` — Alert fatigue patterns: grouping, suppression, flapping
- `references/incident-management.md` — Incident lifecycle, priority tiers, postmortem automation
- `assets/terraform-module/` — Reusable Terraform module template
