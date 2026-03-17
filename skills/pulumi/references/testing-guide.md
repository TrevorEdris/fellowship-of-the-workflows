# Pulumi Testing Guide

## Test Types

| Type | Speed | Cloud Calls | When to Use |
|------|-------|-------------|-------------|
| Unit | Fast (ms) | No | Test resource configuration and Output logic |
| Property | Fast (ms) | No | Generative testing across input space |
| Integration | Slow (minutes) | Yes | Full stack deployment validation |

## Unit Tests (No Cloud Calls)

Unit tests use `pulumi.runtime.setMocks()` to intercept provider calls.

```typescript
// unit.test.ts
import * as pulumi from "@pulumi/pulumi";
import * as aws from "@pulumi/aws";

// Must set mocks BEFORE importing your Pulumi program
pulumi.runtime.setMocks({
  newResource: (args: pulumi.runtime.MockResourceArgs): { id: string; state: any } => {
    return {
      id: `${args.name}-id`,
      state: {
        ...args.inputs,
        // Simulate provider-generated values
        arn: `arn:aws:s3:::${args.inputs.bucket ?? args.name}`,
        region: "us-east-1",
      },
    };
  },
  call: (args: pulumi.runtime.MockCallArgs) => {
    return args.inputs;
  },
}, "test-project", "test-stack", false);

// Import after mocks are set
import { MyStack } from "./my-stack";

describe("MyStack", () => {
  let stack: MyStack;

  before(async () => {
    stack = new MyStack();
  });

  it("creates S3 bucket with versioning", async () => {
    // Verify resource was created with correct config
    const bucket = stack.appBucket;
    const versioning = await bucket.versioning.apply(v => v).promise();
    assert.strictEqual(versioning?.enabled, true);
  });

  it("bucket has correct tags", async () => {
    const tags = await stack.appBucket.tags.apply(t => t).promise();
    assert.strictEqual(tags?.Environment, "test-stack");
    assert.ok(tags?.ManagedBy === "pulumi");
  });

  it("IAM role has correct trust policy", async () => {
    const policy = await stack.appRole.assumeRolePolicy.apply(p => JSON.parse(p));
    const statement = policy.Statement[0];
    assert.strictEqual(statement.Principal.Service, "lambda.amazonaws.com");
  });
});
```

## Property Tests (Generative)

Use fast-check to generate random inputs and verify invariants hold:

```typescript
import fc from "fast-check";
import * as pulumi from "@pulumi/pulumi";

pulumi.runtime.setMocks({ /* ... */ });

import { createBucket } from "./resources";

describe("S3 bucket property tests", () => {
  it("bucket name never exceeds 63 characters", async () => {
    await fc.assert(fc.asyncProperty(
      fc.string({ minLength: 1, maxLength: 30 }),
      fc.constantFrom("dev", "staging", "prod"),
      async (projectName, env) => {
        const bucket = createBucket(projectName, env);
        const name = await bucket.bucket.apply(n => n).promise();
        return name.length <= 63;
      }
    ));
  });

  it("encryption always enabled regardless of environment", async () => {
    await fc.assert(fc.asyncProperty(
      fc.constantFrom("dev", "staging", "prod"),
      async (env) => {
        const bucket = createBucket("my-project", env);
        const encrypted = await bucket.serverSideEncryptionConfiguration
          .apply(c => c !== undefined).promise();
        return encrypted;
      }
    ));
  });
});
```

## Integration Tests (Live Cloud)

Integration tests deploy a real stack, assert against outputs, then destroy.

```typescript
// integration.test.ts
import { LocalWorkspace, Stack } from "@pulumi/pulumi/automation";
import * as aws from "@aws-sdk/client-s3";

const stackName = `test-${process.env.GITHUB_RUN_ID ?? Date.now()}`;

describe("integration: S3 bucket", () => {
  let stack: Stack;

  before(async function () {
    this.timeout(300000); // 5 minutes

    stack = await LocalWorkspace.createOrSelectStack({
      stackName,
      workDir: process.cwd(),
    });

    await stack.up({ onOutput: console.log });
  });

  after(async function () {
    this.timeout(300000);
    await stack.destroy({ onOutput: console.log });
    await stack.workspace.removeStack(stackName);
  });

  it("bucket exists and is versioned", async () => {
    const outputs = await stack.outputs();
    const bucketName = outputs.bucketName.value as string;

    const s3 = new aws.S3Client({});
    const versioning = await s3.send(new aws.GetBucketVersioningCommand({
      Bucket: bucketName,
    }));
    assert.strictEqual(versioning.Status, "Enabled");
  });

  it("API endpoint returns 200", async () => {
    const outputs = await stack.outputs();
    const url = outputs.apiUrl.value as string;
    const response = await fetch(url);
    assert.strictEqual(response.status, 200);
  });
});
```

## Pulumi Automation API

The Automation API enables programmatic stack management for complex test scenarios:

```typescript
import { LocalWorkspace } from "@pulumi/pulumi/automation";

// Create and manage stacks programmatically
const workspace = await LocalWorkspace.create({
  workDir: "/path/to/pulumi/program",
});

const stack = await LocalWorkspace.createOrSelectStack({
  stackName: "test-integration",
  workDir: "/path/to/pulumi/program",
  projectSettings: {
    name: "my-project",
    runtime: "nodejs",
  },
});

await stack.setConfig("aws:region", { value: "us-east-1" });
await stack.up({ onOutput: process.stdout.write.bind(process.stdout) });
const outputs = await stack.outputs();
await stack.destroy();
```

## CI Integration

```yaml
# GitHub Actions integration test job
integration-test:
  runs-on: ubuntu-latest
  permissions:
    id-token: write  # For OIDC
  steps:
    - uses: actions/checkout@v4

    - uses: aws-actions/configure-aws-credentials@v4
      with:
        role-to-assume: ${{ secrets.AWS_ROLE_ARN }}
        aws-region: us-east-1

    - run: npm ci && npm test
      env:
        PULUMI_ACCESS_TOKEN: ${{ secrets.PULUMI_ACCESS_TOKEN }}
        GITHUB_RUN_ID: ${{ github.run_id }}
```

**Always destroy test stacks in CI — use `after()` hooks and CI job cancellation handlers.**
