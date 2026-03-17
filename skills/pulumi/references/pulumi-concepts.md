# Pulumi Core Concepts Reference

## The Pulumi Object Model

| Concept | Description |
|---------|-------------|
| **Project** | A directory with `Pulumi.yaml`; defines the program name and runtime |
| **Stack** | A deployment instance of a project (e.g., `my-infra/dev`, `my-infra/prod`) |
| **Resource** | A cloud resource managed by Pulumi (maps to a provider API) |
| **Output** | A lazily-evaluated value from a resource; type-safe future value |
| **Input** | A value accepted by a resource property; can be `T` or `Output<T>` |
| **Provider** | Plugin that manages cloud resources (aws, azure, gcp, kubernetes, etc.) |
| **Config** | Stack-specific key-value configuration |

## Outputs and Inputs

```typescript
// Output<T> — future value resolved after resource creation
const bucket = new aws.s3.Bucket("my-bucket");
const bucketArn: Output<string> = bucket.arn;
const bucketId: Output<string> = bucket.id;

// Transform an Output
const region = bucketArn.apply(arn => arn.split(":")[3]);

// Combine multiple Outputs
const connectionString = pulumi.all([db.host, db.port])
  .apply(([host, port]) => `postgres://${host}:${port}/mydb`);

// String interpolation with Outputs
const url = pulumi.interpolate`https://${lb.dnsName}/api`;

// Export from stack (visible in pulumi stack output)
export const endpointUrl = url;
```

**Never call `.get()` outside unit tests.** `.get()` returns the resolved value synchronously, which only works when using mocked providers in test mode.

## Resource Options

```typescript
const bucket = new aws.s3.Bucket("my-bucket", {
  versioning: { enabled: true },
}, {
  // Resource options (third argument)
  protect: true,                    // Prevent accidental destroy
  retainOnDelete: true,             // Keep resource even if removed from code
  dependsOn: [otherResource],       // Explicit dependency
  ignoreChanges: ["tags"],          // Ignore drift in specific properties
  import: "existing-bucket-name",   // Import existing resource into state
  provider: awsUsEast1Provider,     // Use non-default provider instance
  parent: this,                     // Parent resource for logical grouping
  aliases: ["urn:pulumi:..."],      // Handle resource renames
});
```

## Stack References (Cross-Stack)

```typescript
// Read outputs from another stack in the same org
const infraStack = new pulumi.StackReference("my-org/infra/prod");

// Get output by name — returns Output<any>
const vpcId = infraStack.getOutput("vpcId");
const vpcIdStr = infraStack.getOutput("vpcId") as pulumi.Output<string>;

// Require output — throws if not found
const subnetIds = infraStack.requireOutput("privateSubnetIds");
```

## Configuration

```typescript
const config = new pulumi.Config();

// Required config (throws if not set)
const dbPassword = config.requireSecret("databasePassword");

// Optional with default
const region = config.get("region") ?? "us-east-1";

// Typed config
const maxRetries = config.getNumber("maxRetries") ?? 3;
const featureFlags = config.getObject<{ enabled: boolean }>("featureFlags");

// Secret config — always use for credentials
// Set with: pulumi config set --secret databasePassword "hunter2"
```

## Resource Naming

```typescript
// Auto-generated name (Pulumi appends random suffix)
const bucket = new aws.s3.Bucket("my-bucket");
// → creates bucket named "my-bucket-a1b2c3d4"

// Explicit name — stable for drift detection
const bucket = new aws.s3.Bucket("my-bucket", {
  bucket: `${pulumi.getProject()}-${pulumi.getStack()}-data`,
  // → creates bucket named "my-infra-prod-data" (stable)
});
```

Use explicit names in environments where drift detection and cross-stack references matter.

## Built-In Functions

```typescript
pulumi.getProject()  // Returns project name from Pulumi.yaml
pulumi.getStack()    // Returns active stack name (e.g., "prod")
pulumi.getOrganization()  // Returns org name (Pulumi Cloud only)

// Conditional on stack
const isProd = pulumi.getStack() === "prod";
const instanceType = isProd ? "t3.large" : "t3.micro";

// Output utilities
pulumi.output(value)        // Wrap a plain value as Output
pulumi.secret(value)        // Mark Output as secret (encrypted in state)
pulumi.all([a, b, c])       // Wait for multiple Outputs
pulumi.interpolate`...`     // String interpolation
```

## Dynamic Providers

For resources without a Pulumi provider, implement a dynamic provider:

```typescript
const randomId = new pulumi.dynamic.Resource("random-id", {
  inputs: { length: 8 },
  outputs: { value: undefined as string | undefined },
  create: async (inputs) => ({
    id: Math.random().toString(36).substring(2),
    outs: { value: Math.random().toString(36).substring(2, inputs.length + 2) },
  }),
}, { provider: undefined });
```

## Transformations

Apply transformations to modify all resources in a stack at deployment time:

```typescript
// Add tags to all AWS resources
pulumi.runtime.registerStackTransformation((args) => {
  if (args.type.startsWith("aws:")) {
    args.props["tags"] = {
      ...args.props["tags"],
      ManagedBy: "pulumi",
      Stack: pulumi.getStack(),
      Project: pulumi.getProject(),
    };
  }
  return { props: args.props, opts: args.opts };
});
```
