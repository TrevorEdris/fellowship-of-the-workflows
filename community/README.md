# Community Skills

Community skills are vendor-specific or niche workflows that are valuable but not universally relevant. They follow the same structure and quality bar as core skills — the distinction is audience, not quality.

## Core vs Community

| | Core Skills | Community Skills |
|---|---|---|
| **Location** | `skills/` | `community/` |
| **Audience** | Universal (any stack) | Specific vendor or niche |
| **Plugin auto-discovery** | Yes | No — requires explicit install |
| **`fotw list` default** | Shown | Shown (with "community" tier label) |
| **`fotw list --tier core`** | Shown | Hidden |

## Available Community Skills

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

## Using Community Skills

**Plugin mode:** Community skills are NOT auto-discovered when loading FOTW as a Claude Code plugin. This keeps plugin-mode context clean for users who don't use these vendors.

To use a community skill in plugin mode, install it explicitly:

```bash
fotw install community/azure ~/my-project --for claude-code
```

**Install mode:** Works the same as core skills:

```bash
fotw install community/pulumi ~/my-project --for cursor
fotw install community/grafana-irm --global --for claude-code
```

**List community skills:**

```bash
fotw list --tier community
fotw list --tier community --tag azure
```

## Contributing a Community Skill

Community skills follow the same authoring guide as core skills (see [CONTRIBUTING.md](../CONTRIBUTING.md)). Place the skill directory here (`community/<name>/SKILL.md`) and it will be picked up by `fotw list` and `fotw validate` automatically.

If a community skill achieves broad adoption (used by >50% of the target audience regardless of vendor preference), consider promoting it to `skills/` via a PR discussion.
