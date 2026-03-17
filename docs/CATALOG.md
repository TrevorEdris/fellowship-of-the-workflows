# Skill Catalog

Full listing of all skills available in Fellowship of the Workflows. Skills in the **community/** tier are vendor-specific and not auto-discovered in plugin mode.

Filter via CLI: `./bin/fotw list --type skill`, `./bin/fotw list --tag aws`, `./bin/fotw list --tier community`

---

## Core Skills

### Infrastructure

| Skill | Tags | Description |
|-------|------|-------------|
| `docker` | `infrastructure` | Author Dockerfiles, Docker Compose configurations, and container optimization patterns |
| `kubernetes` | `infrastructure` | Author Kubernetes manifests, Helm charts, and Kustomize overlays |
| `terraform` | `infrastructure` | Write, review, refactor, and audit Terraform configurations |
| `terragrunt` | `infrastructure` | Design and implement DRY Terragrunt configurations using root inheritance and dependency DAGs |
| `aws-iac` | `aws`, `infrastructure` | Author, review, deploy, and migrate AWS infrastructure (CloudFormation, CDK, SAM) |

### Architecture

| Skill | Tags | Description |
|-------|------|-------------|
| `api-design` | `architecture` | Design REST and GraphQL APIs: endpoint naming, versioning, auth, pagination |
| `aws-serverless` | `aws`, `architecture` | AWS serverless architecture patterns: Lambda, API Gateway, Step Functions, EventBridge |
| `c4-architecture` | `architecture`, `documentation` | Generate C4 model diagrams and architecture documentation |
| `database-schema-designer` | `architecture` | Design SQL and NoSQL schemas: normalization, indexing, migrations |
| `event-driven` | `architecture` | Design event-driven architectures using message brokers and event stores |
| `gcp` | `gcp` | GCP project setup, authentication (ADC/Workload Identity), SDK patterns |
| `gcp-iam` | `gcp`, `security` | Audit and configure GCP IAM: roles, bindings, service accounts, Workload Identity |
| `system-design` | `architecture` | Design and review distributed system architecture |

### Review

| Skill | Tags | Description |
|-------|------|-------------|
| `accessibility-audit` | `review` | WCAG 2.1/2.2 accessibility audit covering all POUR principles |
| `code-review` | `review` | Thorough code review using the Pragmatic Code Review methodology |
| `design-review` | `review` | Design review for front-end changes using Playwright for live testing |
| `performance-optimization` | `review` | Analyze code for performance bottlenecks including N+1, memory leaks, bundle size |
| `refactoring` | `review` | Systematic refactoring: smell detection, extract method, dead code removal |
| `security-review` | `security`, `review` | Security-focused code review to identify HIGH-CONFIDENCE vulnerabilities |
| `work-review` | `review` | Review work accomplished over a time period |

### Documentation

| Skill | Tags | Description |
|-------|------|-------------|
| `agent-md-refactor` | `documentation`, `meta` | Refactor bloated AGENTS.md, CLAUDE.md, or similar agent config files |
| `desloppify` | `documentation` | Identify and remove AI slop from code comments, docs, and commit messages |
| `mermaid-diagrams` | `documentation` | Create flowcharts, sequence diagrams, ERDs, and architecture diagrams |
| `reverse-engineer` | `documentation` | Extract PRDs, design docs, and architecture diagrams from existing code |
| `update-docs` | `documentation` | Sync documentation with code changes; detect stale content |
| `writing-clearly-and-concisely` | `documentation` | Improve prose humans will read: documentation, commit messages, ADRs |

### Meta

| Skill | Tags | Description |
|-------|------|-------------|
| `brainstorm` | `meta` | Structured design thinking: constraint capture, alternatives, trade-offs, ADR |
| `create-persona` | `meta` | Create a new AI assistant persona interactively |
| `orchestrate` | `meta` | Coordinate multiple subagents to complete a large task |
| `plan-validator` | `meta` | Validate implementation plans for completeness, specificity, and actionability |
| `session-handoff` | `meta` | Create handoff documents for AI agent session transitions |
| `session-index` | `meta` | Generate and maintain a session index with cross-session insights |
| `switch-persona` | `meta` | Switch AI assistant personas interactively |

### Incident Response

| Skill | Tags | Description |
|-------|------|-------------|
| `incident-management` | `incident-response` | Cross-platform incident management router: detects tooling and routes accordingly |
| `pagerduty` | `incident-response` | Configure PagerDuty services, escalation policies, on-call schedules |

### Cloud Platforms

| Skill | Tags | Description |
|-------|------|-------------|
| `aws` | `aws` | AWS credential setup, SDK patterns (Go/Python/TypeScript), IAM basics |
| `aws-iam` | `aws`, `security` | AWS IAM: least-privilege policies, roles, trust relationships |

### Observability

| Skill | Tags | Description |
|-------|------|-------------|
| `observability` | `observability` | Instrument, audit, and configure observability for services (OTel, Prometheus, Grafana) |

### Security

| Skill | Tags | Description |
|-------|------|-------------|
| `aws-iam` | `aws`, `security` | AWS IAM policy design, least-privilege, audit |
| `gcp-iam` | `gcp`, `security` | GCP IAM: roles, service accounts, Workload Identity |
| `security-review` | `security`, `review` | Code security audit with HIGH-CONFIDENCE findings only |

### Testing

| Skill | Tags | Description |
|-------|------|-------------|
| `e2e-testing` | `testing` | Scaffold E2E and integration tests using Playwright |
| `systematic-debugging` | `testing` | Structured root-cause analysis for bugs and test failures |
| `test-driven-development` | `testing` | Enforce RED-GREEN-REFACTOR cycle for any implementation |

### Other

| Skill | Tags | Description |
|-------|------|-------------|
| `cicd-pipeline` | `ci-cd` | Generate, optimize, and manage CI/CD pipelines (GitHub Actions, GitLab CI) |
| `git-workflow` | `git` | Interactive git assistant: commits, PRs, branches, conflicts, worktrees, finish |
| `go-patterns` | `go` | Go patterns and idioms: error handling, interfaces, concurrency |
| `python-patterns` | `python` | Python patterns and idioms: typing, dataclasses, async |
| `typescript-patterns` | `typescript` | TypeScript patterns and idioms: generics, utility types, strict mode |
| `chaos-review` | `review` | Review system resilience and identify failure modes |

---

## Community Skills

Vendor-specific skills. Not auto-discovered in plugin mode. Install explicitly with `fotw install community/<name>`.

See [community/README.md](../community/README.md) for the tier philosophy.

| Skill | Tier | Tags | Description |
|-------|------|------|-------------|
| `azure` | community | `azure` | Azure platform: authentication, SDKs, services |
| `azure-functions` | community | `azure`, `architecture` | Azure Functions: triggers, bindings, deployment |
| `azure-iac` | community | `azure`, `infrastructure` | Azure IaC with Bicep and Terraform |
| `better-stack` | community | `observability`, `incident-response` | Better Stack uptime monitors, on-call, status pages |
| `cloud-run` | community | `gcp`, `infrastructure` | Cloud Run services, jobs, Eventarc triggers |
| `gcp-data` | community | `gcp`, `architecture` | GCP data stores: Cloud SQL, Firestore, BigQuery, Spanner |
| `grafana-irm` | community | `observability`, `incident-response` | Grafana Cloud IRM on-call and alerting |
| `incident-io` | community | `incident-response` | incident.io Slack-native incident response |
| `pulumi` | community | `infrastructure` | Pulumi multi-cloud infrastructure programs |
| `rust-patterns` | community | `rust` | Rust patterns and idioms |
| `velocity-forecast` | community | `meta` | Sprint velocity forecasting and capacity planning |
