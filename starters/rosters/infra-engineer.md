---
name: infra-engineer
description: "Infrastructure role — IaC, containers, orchestration, cloud platforms, CI/CD."
tags: [engineering, infrastructure]
allowed-skills:
  - terraform
  - terragrunt
  - kubernetes
  - docker
  - cloud-run
  - aws-iac
  - azure-iac
  - pulumi
  - cicd-pipeline
rules:
  - git-safety
preferred-model: sonnet
---

# Infrastructure Engineer Role

Optimized for infrastructure engineering: IaC authoring, container orchestration, cloud platform configuration, and CI/CD pipeline design.

## Included Skills

- **terraform / terragrunt / pulumi** — Multi-cloud IaC authoring and review
- **kubernetes** — Manifests, Helm charts, Kustomize, RBAC, security contexts
- **docker** — Dockerfiles, Compose, multi-stage builds, image security
- **cloud-run** — GCP serverless, Pub/Sub, Eventarc, Cloud Functions
- **aws-iac / azure-iac** — CloudFormation, CDK, SAM, Bicep, ARM templates
- **cicd-pipeline** — GitHub Actions, GitLab CI, caching, matrix testing

## Deliberately Excluded

- Application-level code review — use `backend` or `frontend` roles
- Security auditing — use `security-sentry` role
