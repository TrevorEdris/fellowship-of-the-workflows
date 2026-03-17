# Workflow Catalog

Full listing of all workflows available in Fellowship of the Workflows. Items in the **community/** tier are vendor-specific and not auto-discovered in plugin mode.

Filter via CLI: `./bin/fotw list`, `./bin/fotw list --tag aws`, `./bin/fotw list --tier community`

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

## Core Rules

Conditional context files auto-translated to all 9 tool formats on install.

| Rule | Description |
|------|-------------|
| `ai-session` | Session documentation structure and directory conventions |
| `cloudformation-conventions` | CloudFormation resource naming, deletion policies, change sets |
| `context-efficiency` | Phase-scoped context loading for token efficiency |
| `discover-plan-implement` | 5-phase QRSPI workflow: Question, Research, Structure, Plan, Implement |
| `event-driven-conventions` | Event-driven architecture patterns and messaging idioms |
| `git-safety` | Git safety rules: branch protection, commit hygiene, push guards |
| `go-patterns` | Go error handling, interfaces, concurrency patterns |
| `incident-management-conventions` | Incident severity levels, escalation, postmortem conventions |
| `model-selection` | Task complexity → model guidance (haiku/sonnet/opus) |
| `multi-repo-safety` | Multi-repo boundary rules and cross-repo change discipline |
| `no-brute-force-debugging` | Root-cause-first debugging discipline; three-fix limit |
| `observability-conventions` | Observability naming, cardinality, RED method conventions |
| `output-style` | Response formatting: concise, bullets, no filler phrases |
| `persona-integration` | Persona system: voice/style at runtime via persona.yaml |
| `tdd-enforcement` | Iron Law: no production code without a failing test first |

---

## Core Agents

Specialist subagents auto-discovered in plugin mode.

| Agent | Domain |
|-------|--------|
| `accessibility-audit` | WCAG 2.1/2.2 POUR audit with Playwright browser testing |
| `ascii-ui-mockup-generator` | Text-based UI wireframes and terminal UI mockups |
| `chaos-engineer` | Adversarial failure mode and resilience review |
| `codebase-pattern-finder` | Pattern detection and consistency checking at scale |
| `design-review` | Visual design review with Playwright live testing |
| `desloppify` | AI slop detection and removal from code and docs |
| `documentation-sync` | Post-implementation doc sync and staleness audit |
| `e2e-test-reviewer` | E2E/integration test quality review |
| `general-purpose` | Fallback catch-all for broad or multi-domain tasks |
| `mermaid-diagram-specialist` | Architecture, sequence, flowchart, ERD diagrams |
| `multi-agent-orchestrator` | Multi-agent task decomposition and delegation |
| `performance-optimization` | N+1, caching, bundle size, algorithmic complexity |
| `pragmatic-code-review` | PR review using Pragmatic Quality framework |
| `refactoring-specialist` | Code smell detection and safe refactoring execution |
| `scope-analyzer` | Read-only codebase reverse engineering |
| `security-review` | HIGH-CONFIDENCE vulnerability analysis |
| `system-design-reviewer` | Distributed systems architecture review |
| `systematic-debugger` | Root cause analysis, read-only investigation |
| `tdd-enforcer` | RED-GREEN-REFACTOR cycle gating |
| `ui-ux-designer` | Design system specs, component design, UX flows |

---

## Community Workflows

Vendor-specific. Not auto-discovered in plugin mode. Install explicitly.

See [community/README.md](../community/README.md) for install instructions and the tier philosophy.

### Community Skills

| Skill | Tags | Description |
|-------|------|-------------|
| `azure` | `azure` | Azure platform: authentication, SDKs, services |
| `azure-functions` | `azure`, `architecture` | Azure Functions: triggers, bindings, deployment |
| `azure-iac` | `azure`, `infrastructure` | Azure IaC with Bicep and Terraform |
| `better-stack` | `observability`, `incident-response` | Better Stack uptime monitors, on-call, status pages |
| `cloud-run` | `gcp`, `infrastructure` | Cloud Run services, jobs, Eventarc triggers |
| `gcp-data` | `gcp`, `architecture` | GCP data stores: Cloud SQL, Firestore, BigQuery, Spanner |
| `grafana-irm` | `observability`, `incident-response` | Grafana Cloud IRM on-call and alerting |
| `incident-io` | `incident-response` | incident.io Slack-native incident response |
| `pulumi` | `infrastructure` | Pulumi multi-cloud infrastructure programs |
| `rust-patterns` | `rust` | Rust patterns and idioms |
| `velocity-forecast` | `meta` | Sprint velocity forecasting and capacity planning |

### Community Rules

| Rule | Description |
|------|-------------|
| `azure-patterns` | Azure SDK patterns, Managed Identity, common service idioms |
| `cdk-conventions` | AWS CDK L2 constructs, stack organization, cdk-nag patterns |
| `dockerfile-conventions` | Multi-stage build patterns, layer optimization, security hardening |
| `kubernetes-conventions` | Resource limits, probes, security contexts, RBAC patterns |
| `pagerduty-conventions` | PagerDuty service design and escalation policy conventions |
| `pulumi-conventions` | Pulumi Output/Input discipline, stack naming, no-local-backend |
| `python-patterns` | Python typing, dataclasses, async patterns, testing idioms |
| `rust-patterns` | Rust error handling, ownership idioms, concurrency patterns |

### Community Agents

| Agent | Domain |
|-------|--------|
| `aws-architect` | AWS Well-Architected reviews and service selection |
| `aws-iac-specialist` | CloudFormation, CDK, SAM authoring and CFN→CDK migration |
| `aws-iam-auditor` | IAM policy analysis, privilege escalation, CIS compliance |
| `azure-architect` | Azure service selection and WAF alignment |
| `better-stack-specialist` | Better Stack monitors, on-call, status pages |
| `cloud-run-specialist` | Cloud Run, Cloud Functions, Pub/Sub, Eventarc |
| `datadog-instrumentation` | Datadog APM, DogStatsD, Terraform monitors/SLOs |
| `gcp-iam-auditor` | GCP IAM audit and Workload Identity Federation |
| `grafana-irm-specialist` | Grafana Cloud IRM on-call and alert routing |
| `incident-io-specialist` | incident.io incident response and Terraform |
| `otel-instrumentation` | OTel SDK, Collector, Prometheus, Grafana dashboards |
| `pagerduty-config` | PagerDuty services, escalation policies, Terraform |
| `pulumi-specialist` | Pulumi programs (TS/Python/Go/C#) and CrossGuard |
| `terraform-specialist` | Terraform modules, state, security audit |
| `terragrunt-specialist` | Terragrunt DRY configs, dependency DAGs, multi-account |
