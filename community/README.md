# Community Workflows

Community workflows are vendor-specific or niche items that are valuable but not universally relevant. They follow the same structure and quality bar as core workflows — the distinction is audience, not quality.

## Core vs Community

| | Core | Community |
|---|---|---|
| **Location** | `skills/`, `rules/`, `agents/` | `community/skills/`, `community/rules/`, `community/agents/` |
| **Audience** | Universal (any stack) | Specific vendor or niche |
| **Plugin auto-discovery** | Yes | No — requires explicit install |
| **`fotw list` default** | Shown | Shown (with "community" tier label) |
| **`fotw list --tier core`** | Shown | Hidden |

## Community Skills

Vendor-specific executable workflow packages.

| Skill | Tags | Description |
|-------|------|-------------|
| `azure` | `azure` | Azure platform guidance: authentication, SDKs, services |
| `azure-functions` | `azure`, `architecture` | Azure Functions: triggers, bindings, deployment |
| `azure-iac` | `azure`, `infrastructure` | Azure IaC with Bicep and Terraform |
| `better-stack` | `observability`, `incident-response` | Better Stack uptime monitors and on-call |
| `cloud-run` | `gcp`, `infrastructure` | Cloud Run services, jobs, and Eventarc |
| `gcp-data` | `gcp`, `architecture` | GCP data stores: Cloud SQL, Firestore, BigQuery |
| `grafana-irm` | `observability`, `incident-response` | Grafana Cloud IRM on-call and alerting |
| `incident-io` | `incident-response` | incident.io Slack-native incident response |
| `pulumi` | `infrastructure` | Pulumi multi-cloud infrastructure programs |
| `rust-patterns` | `rust` | Rust patterns and idioms |
| `velocity-forecast` | `meta` | Sprint velocity forecasting and capacity planning |

## Community Rules

Vendor-specific coding conventions and patterns. Auto-translated to all tool formats on install.

| Rule | Description |
|------|-------------|
| `azure-patterns` | Azure SDK patterns, Managed Identity, common service idioms |
| `cdk-conventions` | AWS CDK L2 constructs, stack organization, cdk-nag patterns |
| `dockerfile-conventions` | Multi-stage build patterns, layer optimization, security hardening |
| `kubernetes-conventions` | Resource limits, probes, security contexts, RBAC patterns |
| `pagerduty-conventions` | PagerDuty service design, escalation policy conventions |
| `pulumi-conventions` | Pulumi Output/Input discipline, stack naming, no-local-backend |
| `python-patterns` | Python typing, dataclasses, async patterns, testing idioms |
| `rust-patterns` | Rust error handling, ownership idioms, concurrency patterns |

## Community Agents

Vendor/platform specialist subagents. Not auto-discovered in plugin mode.

| Agent | Domain |
|-------|--------|
| `aws-architect` | AWS Well-Architected reviews |
| `aws-iac-specialist` | CloudFormation, CDK, SAM authoring |
| `aws-iam-auditor` | IAM policy analysis and audit |
| `azure-architect` | Azure service selection and WAF alignment |
| `better-stack-specialist` | Better Stack monitors and status pages |
| `cloud-run-specialist` | Cloud Run, Cloud Functions, Pub/Sub |
| `datadog-instrumentation` | Datadog APM, DogStatsD, Terraform monitors |
| `gcp-iam-auditor` | GCP IAM audit and Workload Identity |
| `grafana-irm-specialist` | Grafana Cloud IRM on-call and alerting |
| `incident-io-specialist` | incident.io incident response |
| `otel-instrumentation` | OTel SDK, Collector, Prometheus, Grafana |
| `pagerduty-config` | PagerDuty services, schedules, Terraform |
| `pulumi-specialist` | Pulumi programs and CrossGuard |
| `terraform-specialist` | Terraform modules, state, security audit |
| `terragrunt-specialist` | Terragrunt DRY configs, dependency DAGs |

## Using Community Workflows

**Plugin mode:** Community workflows are NOT auto-discovered when loading FOTW as a Claude Code plugin. This keeps plugin-mode context clean for users who don't use these vendors.

**Install explicitly:**

```bash
# Skills
fotw install community/azure ~/my-project --for claude-code
fotw install community/pulumi ~/my-project --for cursor

# Rules
fotw install rules/azure-patterns ~/my-project --for claude-code
fotw install rules/dockerfile-conventions --global --for claude-code

# Agents
fotw install agents/terraform-specialist ~/my-project --for claude-code
```

**List community workflows:**

```bash
fotw list --tier community
fotw list --tier community --type rule
fotw list --tier community --type agent
fotw list --tier community --tag azure
```

## Contributing a Community Workflow

Community workflows follow the same authoring guide as core workflows (see [CONTRIBUTING.md](../CONTRIBUTING.md)).

- **Skills:** Place the skill directory at `community/<name>/SKILL.md`
- **Rules:** Place the rule file at `community/rules/<name>.mdc`
- **Agents:** Place the agent file at `community/agents/<name>.md`

All community workflows are auto-picked up by `fotw list` and `fotw validate`.

If a community workflow achieves broad adoption regardless of vendor preference, consider promoting it to the core tier via a PR discussion.
