---
name: pulumi
description: "Build and manage multi-cloud infrastructure with Pulumi. Supports TypeScript, Python, Go, C#, YAML. Modes: generate, preview, migrate (from Terraform/CFN), policy, test. Use for any Pulumi IaC task."
context: fork
agent: pulumi-specialist
allowed-tools: Bash, Read, Glob, Grep, Write
model: sonnet
argument-hint: "[generate|preview|migrate|policy|test]"
user-invocable: true
tags: [infrastructure]
---

# Pulumi

Build and manage multi-cloud infrastructure using Pulumi's general-purpose programming model.

---

## When to Use

- Writing new Pulumi programs (TypeScript, Python, Go, C#)
- Previewing changes with `pulumi preview` before applying
- Migrating Terraform HCL or CloudFormation to Pulumi
- Writing CrossGuard policy packs for compliance enforcement
- Testing Pulumi programs (unit, property, integration)
- Configuring state backends (Pulumi Cloud, S3, GCS, Azure Blob)
- Multi-cloud infrastructure requiring shared abstractions across AWS + Azure + GCP

**Out of scope:** CI/CD pipeline definition (use `/cicd-pipeline`), Terraform-only workflows (use `/terraform`), AWS-native CloudFormation/CDK (use `/aws-iac`).

**MCP Integration:** If `@pulumi/mcp-server` is configured, this skill can invoke `pulumi preview`, `pulumi up`, and `stack_output` directly via MCP tools.

---

## Quick Start

```
/pulumi generate    # Scaffold new Pulumi program for detected or specified cloud
/pulumi preview     # Run pulumi preview and explain planned changes
/pulumi migrate     # Convert Terraform HCL or CloudFormation to Pulumi
/pulumi policy      # Author CrossGuard policy pack for compliance rules
/pulumi test        # Generate unit and integration tests for Pulumi program
```

No argument? Detects `Pulumi.yaml` and active stack; defaults to `preview` if project exists, `generate` if not.

---

## Context

PULUMI PROJECT:
```
!`cat Pulumi.yaml 2>/dev/null || echo "No Pulumi.yaml found"`
```

ACTIVE STACK:
```
!`pulumi stack --show-name 2>/dev/null || echo "Not logged in or no stack selected"`
```

BACKEND:
```
!`pulumi whoami -v 2>/dev/null || echo "Not logged in to Pulumi"`
```

STACK CONFIG:
```
!`ls Pulumi.*.yaml 2>/dev/null | head -5`
```

LANGUAGE DETECTION:
```
!`ls package.json go.mod pyproject.toml *.csproj 2>/dev/null | head -5`
```

---

## Mode: generate

Scaffold a new Pulumi program.

**Steps:**
1. Detect or ask for: target cloud (AWS/Azure/GCP/multi-cloud), language (TypeScript default), resource set
2. Create `Pulumi.yaml` with project name and runtime
3. Create `Pulumi.<stack>.yaml` for dev stack configuration
4. Scaffold main program using provider SDK resources:
   - Prefer named resource exports for stack reference consumption
   - Tag all resources with `pulumi.getStack()` environment tag
   - Use `Output<T>` types; never call `.get()` in production code
5. Configure state backend guidance (see `references/state-backends.md`)
6. Provide `pulumi login`, `pulumi stack init`, `pulumi up` next steps

**Stack naming convention:** `<project>/<env>` (e.g., `my-infra/prod`, `my-infra/staging`)

**Asset templates:**
- `assets/aws-starter/` — TypeScript Pulumi program for AWS
- `assets/policy-pack-template/` — CrossGuard policy pack starter

---

## Mode: preview

Run `pulumi preview` and interpret planned changes.

**Steps:**
1. Verify active stack with `pulumi stack`
2. Run `pulumi preview --diff` (or via MCP `preview` tool if available)
3. Summarize:
   - Resources to create / update / replace / delete
   - **Flag replacements** — destroy + recreate; requires explicit acknowledgment
   - **Flag stateful resource changes** (databases, storage, queues)
4. Check for drift: run `pulumi refresh --skip-preview` recommendation if drift suspected
5. For production stacks: recommend requiring `--expect-no-changes` in CI to detect unreviewed drift

---

## Mode: migrate

Convert Terraform HCL or CloudFormation to Pulumi.

**For Terraform migration:**
1. Use `pulumi convert --from terraform --language typescript` (or via MCP `convert` tool)
2. Review generated code for:
   - `pulumi.interpolate` vs template literals
   - `apply()` chains for Output dependencies
   - Provider configuration (env vars vs config)
3. Replace Terraform workspaces with Pulumi stacks
4. Replace `terraform_remote_state` with `pulumi.StackReference`

**For CloudFormation migration:**
1. Use `pulumi convert --from cloudformation --language typescript`
2. Map CFN intrinsic functions to Pulumi Output methods
3. Replace `Fn::ImportValue` with `pulumi.StackReference`
4. Convert Parameters to `pulumi.Config` lookups

Reference: `references/migration-from-terraform.md`

---

## Mode: policy

Author CrossGuard policy packs for compliance enforcement.

**Steps:**
1. Define policy pack with `PolicyPack` in `index.ts`
2. Use `validateResourceOfType` for type-specific rules
3. Set enforcement levels: `advisory` (log only), `mandatory` (block), `remediate` (auto-fix)
4. Common policy templates:
   - No public S3 bucket ACLs
   - Encryption at rest required for storage resources
   - Required resource tags (environment, owner, cost-center)
   - No publicly accessible database instances
5. Package for distribution: `pulumi policy publish`

Reference: `references/crossguard-patterns.md`
Asset: `assets/policy-pack-template/index.ts`

---

## Mode: test

Generate tests for a Pulumi program.

**Unit tests** (no cloud calls):
- Mock provider responses with `pulumi.runtime.setMocks()`
- Assert resource properties and Output values
- Test configuration-driven branching

**Property tests** (generative):
- Use fast-check or hypothesis to generate input variations
- Assert invariants hold across input space

**Integration tests** (live cloud):
- `pulumi up --stack test-<id>` → run assertions against outputs → `pulumi destroy`
- Use in CI with short-lived stacks; never test against prod stack

Reference: `references/testing-guide.md`

---

## Key References

| Reference | Contents |
|-----------|----------|
| `references/pulumi-concepts.md` | Stack, Project, Output/Input, Resource options, StackReference |
| `references/state-backends.md` | Pulumi Cloud vs S3 vs GCS vs Azure Blob; backend selection guide |
| `references/crossguard-patterns.md` | Policy packs, enforcement levels, remediation, publishing |
| `references/testing-guide.md` | Unit, property, integration test patterns with code examples |
| `references/migration-from-terraform.md` | pulumi convert, Output mapping, workspace → stack migration |
| `references/multi-cloud-patterns.md` | Cross-provider resource dependencies, shared config patterns |

## Asset Templates

| Asset | Purpose |
|-------|---------|
| `assets/aws-starter/index.ts` | TypeScript Pulumi program targeting AWS |
| `assets/aws-starter/Pulumi.yaml` | Project manifest for AWS starter |
| `assets/policy-pack-template/index.ts` | CrossGuard policy pack with common rules |

## Scripts

| Script | Purpose |
|--------|---------|
| `scripts/detect-backend.sh` | Detect configured state backend from environment |
