# Pulumi Multi-Cloud Patterns

## When Multi-Cloud Makes Sense

Use Pulumi's multi-cloud capability when:
- Applications span multiple cloud providers (e.g., AWS compute + GCP AI/ML)
- Disaster recovery requires active-active across clouds
- Organization policy mandates cloud independence
- Migrating between clouds incrementally

Avoid multi-cloud complexity when a single cloud meets requirements — shared abstractions add cognitive overhead without benefit.

## Provider Configuration

```typescript
import * as aws from "@pulumi/aws";
import * as azure from "@pulumi/azure-native";
import * as gcp from "@pulumi/gcp";

// Configure providers
const awsProvider = new aws.Provider("aws-primary", {
  region: "us-east-1",
});

const gcpProvider = new gcp.Provider("gcp-primary", {
  project: "my-gcp-project",
  region: "us-central1",
});

// Use specific provider for a resource
const s3Bucket = new aws.s3.Bucket("data", {}, { provider: awsProvider });
const gcsBucket = new gcp.storage.Bucket("data-backup", {
  location: "US",
}, { provider: gcpProvider });
```

## Cross-Provider Data Flow

```typescript
// Write to S3, replicate ARN to GCP Secret Manager
const bucket = new aws.s3.Bucket("primary-data", {
  versioning: { enabled: true },
});

// Pass AWS resource info to GCP configuration
const bucketArnSecret = new gcp.secretmanager.Secret("aws-bucket-arn", {
  secretId: "aws-primary-bucket-arn",
}, { provider: gcpProvider });

new gcp.secretmanager.SecretVersion("aws-bucket-arn-version", {
  secret: bucketArnSecret.id,
  secretData: bucket.arn,  // Output<string> flows across providers
}, { provider: gcpProvider });
```

## Shared Configuration Abstraction

```typescript
// config.ts — shared across all providers
export interface AppConfig {
  environment: string;
  region: {
    aws: string;
    gcp: string;
    azure: string;
  };
  replication: boolean;
}

const config = new pulumi.Config();

export const appConfig: AppConfig = {
  environment: pulumi.getStack(),
  region: {
    aws: config.get("awsRegion") ?? "us-east-1",
    gcp: config.get("gcpRegion") ?? "us-central1",
    azure: config.get("azureRegion") ?? "eastus",
  },
  replication: config.getBoolean("replication") ?? false,
};
```

## Component Resource for Multi-Cloud Abstraction

```typescript
// multi-cloud-storage.ts — abstract storage across clouds
export interface MultiCloudStorageArgs {
  name: string;
  replicationEnabled: boolean;
}

export class MultiCloudStorage extends pulumi.ComponentResource {
  public readonly primaryBucketName: pulumi.Output<string>;
  public readonly replicaBucketName: pulumi.Output<string> | undefined;

  constructor(
    name: string,
    args: MultiCloudStorageArgs,
    opts?: pulumi.ComponentResourceOptions
  ) {
    super("my-infra:storage:MultiCloudStorage", name, {}, opts);

    const childOpts = { parent: this };

    // Primary on AWS
    const primary = new aws.s3.Bucket(`${name}-primary`, {
      versioning: { enabled: true },
      tags: { ManagedBy: "pulumi", Name: args.name },
    }, childOpts);

    this.primaryBucketName = primary.id;

    // Replica on GCP (optional)
    if (args.replicationEnabled) {
      const replica = new gcp.storage.Bucket(`${name}-replica`, {
        location: "US",
        versioning: { enabled: true },
        labels: { managed_by: "pulumi", name: args.name },
      }, childOpts);

      this.replicaBucketName = replica.id;
    }

    this.registerOutputs({
      primaryBucketName: this.primaryBucketName,
      replicaBucketName: this.replicaBucketName,
    });
  }
}
```

## Cross-Stack References Across Clouds

Each cloud has its own Pulumi stack; share data via `StackReference`:

```typescript
// In AWS stack (org/aws-infra/prod)
export const vpcId = vpc.id;
export const privateSubnetIds = privateSubnets.map(s => s.id);

// In GCP stack, read AWS outputs
const awsInfra = new pulumi.StackReference("my-org/aws-infra/prod");
const awsVpcId = awsInfra.getOutput("vpcId");

// Use in GCP resources (e.g., for VPN tunnel peering)
const vpnTunnel = new gcp.compute.VpnTunnel("aws-to-gcp", {
  peerIp: awsInfra.getOutput("vpnGatewayIp") as pulumi.Output<string>,
  // ...
}, { provider: gcpProvider });
```

## Multi-Cloud Decision Matrix

| Scenario | Approach |
|----------|----------|
| AWS primary + GCP for BigQuery | Separate stacks, StackReference for VPN/networking outputs |
| Kubernetes across clouds | Single Pulumi program with multiple kubernetes providers |
| DNS across clouds | Route53 + Cloud DNS managed in same program for atomic updates |
| Secrets federation | Write to AWS Secrets Manager; GCP/Azure read via cross-cloud service accounts |

## Avoiding Multi-Cloud Pitfalls

- **Eventual consistency across providers** — Resources in different clouds do not have atomic deployment semantics; a failure mid-deploy leaves partial state
- **Implicit ordering** — Pulumi infers dependency from Output usage; make cross-cloud dependencies explicit with `dependsOn`
- **Provider version pinning** — Pin all provider versions; multi-cloud programs are more sensitive to provider changes
- **Cost visibility** — Multi-cloud costs are harder to attribute; tag everything with `Project` and `Stack` for cost allocation
