# vendors/

Vendor-specific workflows for PagerDuty, Better Stack, Grafana IRM, and incident.io.

Not auto-discovered in plugin mode. Install explicitly.

## Contents

```
vendors/
├── skills/       Vendor-specific skills
├── rules/        Vendor-specific rules
└── agents/       Vendor-specific subagents
```

## Skills

| Skill | Tags | Description |
|-------|------|-------------|
| `better-stack` | `observability`, `incident-response` | Better Stack uptime monitors, on-call, status pages |
| `grafana-irm` | `observability`, `incident-response` | Grafana Cloud IRM on-call and alerting |
| `incident-io` | `incident-response` | incident.io Slack-native incident response |
| `pagerduty` | `incident-response` | PagerDuty services, escalation policies, on-call schedules |

## Rules

| Rule | Description |
|------|-------------|
| `pagerduty-conventions` | PagerDuty service design and escalation policy conventions |

## Agents

| Agent | Domain |
|-------|--------|
| `better-stack-specialist` | Better Stack monitors, on-call, status pages |
| `datadog-instrumentation` | Datadog APM, DogStatsD, Terraform monitors/SLOs |
| `grafana-irm-specialist` | Grafana Cloud IRM on-call and alert routing |
| `incident-io-specialist` | incident.io incident response and Terraform |
| `pagerduty-config` | PagerDuty services, escalation policies, Terraform |

## Install

```bash
# Install a skill
./bin/fotw install vendors/skills/pagerduty ~/my-project --for claude-code

# Install a rule
./bin/fotw install vendors/rules/pagerduty-conventions ~/my-project --for claude-code

# Install an agent (Claude Code only)
./bin/fotw install vendors/agents/pagerduty-config ~/my-project --for claude-code
```

## Why separate?

Not every team uses PagerDuty. Not every team uses Grafana. Vendor lock-in is a real concern — workflows specific to a commercial tool shouldn't clutter the core directory for teams that don't use it. Install only the vendors your team has adopted.
