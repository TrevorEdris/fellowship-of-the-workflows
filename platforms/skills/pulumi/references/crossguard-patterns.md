# CrossGuard Policy Patterns

## Policy Pack Structure

```
my-policy-pack/
├── index.ts          # Policy pack definition
├── package.json
├── tsconfig.json
└── PulumiPolicy.yaml # Policy pack manifest
```

```yaml
# PulumiPolicy.yaml
name: my-org-policies
runtime: nodejs
description: Organization-wide compliance policies
```

```json
// package.json
{
  "name": "my-org-policies",
  "dependencies": {
    "@pulumi/policy": "^1.0.0",
    "@pulumi/aws": "^6.0.0"
  }
}
```

## PolicyPack Anatomy

```typescript
import { PolicyPack, validateResourceOfType, ReportViolation } from "@pulumi/policy";
import * as aws from "@pulumi/aws";

new PolicyPack("my-org-policies", {
  policies: [
    // ... policy definitions
  ],
});
```

## Common Policy Patterns

### Required Tags

```typescript
{
  name: "required-tags",
  description: "All resources must have required tags",
  enforcementLevel: "mandatory",
  validateResource: (args, reportViolation) => {
    const requiredTags = ["Environment", "Project", "Owner"];
    const tags = (args.props as any).tags ?? {};
    for (const tag of requiredTags) {
      if (!tags[tag]) {
        reportViolation(`Resource is missing required tag: ${tag}`);
      }
    }
  },
}
```

### No Public S3 Buckets

```typescript
{
  name: "s3-no-public-access",
  description: "S3 buckets must block all public access",
  enforcementLevel: "mandatory",
  validateResource: validateResourceOfType(aws.s3.Bucket, (bucket, args, reportViolation) => {
    const publicAccessBlock = bucket.publicAccessBlockConfiguration;
    if (!publicAccessBlock ||
        !publicAccessBlock.blockPublicAcls ||
        !publicAccessBlock.blockPublicPolicy ||
        !publicAccessBlock.ignorePublicAcls ||
        !publicAccessBlock.restrictPublicBuckets) {
      reportViolation("S3 bucket must have all public access blocks enabled");
    }
  }),
}
```

### Storage Encryption Required

```typescript
{
  name: "s3-encryption-required",
  description: "S3 buckets must have server-side encryption enabled",
  enforcementLevel: "mandatory",
  validateResource: validateResourceOfType(aws.s3.BucketServerSideEncryptionConfigurationV2, (config, args, reportViolation) => {
    const rules = config.rules ?? [];
    if (rules.length === 0) {
      reportViolation("S3 bucket must have server-side encryption configured");
    }
  }),
}
```

### No Public RDS Instances

```typescript
{
  name: "rds-no-public-access",
  description: "RDS instances must not be publicly accessible",
  enforcementLevel: "mandatory",
  validateResource: validateResourceOfType(aws.rds.Instance, (instance, args, reportViolation) => {
    if (instance.publiclyAccessible) {
      reportViolation("RDS instance must not be publicly accessible");
    }
  }),
}
```

### Enforce Deletion Protection

```typescript
{
  name: "rds-deletion-protection",
  description: "RDS instances must have deletion protection enabled in prod",
  enforcementLevel: "advisory",  // Advisory so dev/staging are warned not blocked
  validateResource: validateResourceOfType(aws.rds.Instance, (instance, args, reportViolation) => {
    if (!instance.deletionProtection) {
      reportViolation("RDS instance should have deletion protection enabled");
    }
  }),
}
```

### Instance Type Allow List

```typescript
{
  name: "ec2-approved-instance-types",
  description: "EC2 instances must use approved instance types",
  enforcementLevel: "mandatory",
  validateResource: validateResourceOfType(aws.ec2.Instance, (instance, args, reportViolation) => {
    const approvedTypes = ["t3.micro", "t3.small", "t3.medium", "t3.large", "m5.large", "m5.xlarge"];
    if (!approvedTypes.includes(instance.instanceType ?? "")) {
      reportViolation(`EC2 instance type ${instance.instanceType} is not in the approved list: ${approvedTypes.join(", ")}`);
    }
  }),
}
```

## Enforcement Levels

```typescript
// Advisory — log violation, do not block pulumi up
enforcementLevel: "advisory"

// Mandatory — block pulumi up on violation
enforcementLevel: "mandatory"

// Remediate — auto-fix the non-compliant value before creation
enforcementLevel: "remediate"
```

**Remediation example:**
```typescript
{
  name: "enforce-encryption-tag",
  enforcementLevel: "remediate",
  validateResource: (args, reportViolation) => {
    // With remediate, return new props to fix the violation
    if (!(args.props as any).tags?.Encrypted) {
      return {
        props: {
          ...args.props,
          tags: { ...(args.props as any).tags, Encrypted: "true" },
        },
      };
    }
  },
}
```

## Running Policy Packs

```bash
# Run policy pack locally (advisory only — does not block)
pulumi preview --policy-pack ./my-policy-pack

# Run with enforcement
pulumi up --policy-pack ./my-policy-pack

# Run multiple policy packs
pulumi up \
  --policy-pack ./required-tags \
  --policy-pack ./security-policies

# Run policy pack from Pulumi Cloud registry
pulumi up --policy-pack-config '{"required-tags": {"enforcementLevel": "mandatory"}}'
```

## Publishing Policy Packs (Pulumi Cloud)

```bash
# Publish to Pulumi Cloud org
pulumi policy publish --org my-org

# Enable for a stack
pulumi policy enable my-org/my-org-policies latest

# Disable
pulumi policy disable my-org/my-org-policies
```

## Testing Policy Packs

```typescript
// policy-pack.test.ts
import { PolicyPackArgs } from "@pulumi/policy";

describe("required-tags policy", () => {
  it("reports violation for resource missing tags", () => {
    const violations: string[] = [];
    const reportViolation = (msg: string) => violations.push(msg);

    // Simulate resource without tags
    requiredTagsPolicy.validateResource({
      type: "aws:s3/bucket:Bucket",
      props: { bucket: "my-bucket" },  // No tags
      name: "test-bucket",
      urn: "urn:pulumi:test::project::aws:s3/bucket:Bucket::test-bucket",
      opts: {},
    }, reportViolation);

    expect(violations).toContain("Resource is missing required tag: Environment");
  });
});
```
