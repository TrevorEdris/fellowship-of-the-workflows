# platforms/

Platform-specific workflows for AWS, GCP, Azure, Docker, Kubernetes, Terraform, and more.

Not auto-discovered in plugin mode. Install explicitly.

## Contents

```
platforms/
├── skills/       Platform-specific skills
├── rules/        Platform-specific rules
└── agents/       Platform-specific subagents
```

## Skills

| Skill | Tags | Description |
|-------|------|-------------|
| `aws` | `aws` | AWS credential setup, SDK patterns, CLI workflows |
| `aws-iac` | `aws`, `infrastructure` | CloudFormation, CDK, SAM authoring and review |
| `aws-iam` | `aws`, `security` | IAM policies, least-privilege, Secrets Manager, KMS |
| `aws-serverless` | `aws`, `architecture` | Lambda, Step Functions, EventBridge, SQS/SNS patterns |
| `azure` | `azure` | Azure authentication, CLI, IaC decision tree |
| `azure-functions` | `azure`, `architecture` | Azure Functions triggers, bindings, Durable Functions |
| `azure-iac` | `azure`, `infrastructure` | Azure Bicep and ARM templates |
| `cloud-run` | `gcp`, `infrastructure` | Cloud Run services, jobs, Eventarc triggers |
| `docker` | `infrastructure` | Dockerfiles, Docker Compose, container optimization |
| `gcp` | `gcp` | GCP project setup, authentication, gcloud CLI |
| `gcp-data` | `gcp`, `architecture` | Cloud SQL, Firestore, BigQuery, Spanner, GCS |
| `gcp-iam` | `gcp`, `security` | GCP IAM roles, service accounts, Workload Identity |
| `kubernetes` | `infrastructure` | Kubernetes manifests, Helm charts, Kustomize overlays |
| `pulumi` | `infrastructure` | Pulumi multi-cloud infrastructure programs |
| `terraform` | `infrastructure` | Terraform modules, state, providers, testing |
| `terragrunt` | `infrastructure` | DRY Terragrunt configurations, dependency DAGs |

## Rules

| Rule | Description |
|------|-------------|
| `azure-patterns` | Azure SDK patterns, Managed Identity, common service idioms |
| `cdk-conventions` | AWS CDK L2 constructs, stack organization, cdk-nag patterns |
| `cloudformation-conventions` | CloudFormation resource naming, deletion policies, change sets |
| `dockerfile-conventions` | Multi-stage build patterns, layer optimization, security hardening |
| `kubernetes-conventions` | Resource limits, probes, security contexts, RBAC patterns |
| `pulumi-conventions` | Pulumi Output/Input discipline, stack naming, no-local-backend |
| `terraform-conventions` | Terraform module structure, state, naming conventions |

## Agents

| Agent | Domain |
|-------|--------|
| `aws-architect` | AWS Well-Architected reviews and service selection |
| `aws-iac-specialist` | CloudFormation, CDK, SAM authoring and CFN→CDK migration |
| `aws-iam-auditor` | IAM policy analysis, privilege escalation, CIS compliance |
| `azure-architect` | Azure service selection and WAF alignment |
| `cloud-run-specialist` | Cloud Run, Cloud Functions, Pub/Sub, Eventarc |
| `gcp-iam-auditor` | GCP IAM audit and Workload Identity Federation |
| `otel-instrumentation` | OTel SDK, Collector, Prometheus, Grafana dashboards |
| `pulumi-specialist` | Pulumi programs (TS/Python/Go/C#) and CrossGuard |
| `terraform-specialist` | Terraform modules, state, security audit |
| `terragrunt-specialist` | Terragrunt DRY configs, dependency DAGs, multi-account |

## Install

```bash
# Install a skill
./bin/fotw install platforms/skills/terraform ~/my-project --for claude-code

# Install a rule
./bin/fotw install platforms/rules/terraform-conventions ~/my-project --for claude-code

# Install an agent (Claude Code only)
./bin/fotw install platforms/agents/terraform-specialist ~/my-project --for claude-code
```

## Why separate?

Not every team uses AWS. Not every team uses Kubernetes. Platform-specific workflows in the core directories would add noise for users on a different stack. Install only the platforms your team uses.
