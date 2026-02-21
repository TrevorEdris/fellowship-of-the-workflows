# Migration from Terraform to Pulumi

## When to Migrate

**Migrate when:**
- Team needs full programming language features (loops, conditionals, type safety, abstractions)
- Multi-cloud programs share logic across providers
- Policy-as-code (CrossGuard) is required at provisioning time
- Terraform HCL complexity is growing beyond maintainability

**Don't migrate when:**
- Existing Terraform is working and the team is productive
- The migration would deliver no new capability
- Large Terraform codebase with custom providers not yet available in Pulumi

## Automated Conversion

```bash
# Convert Terraform HCL to TypeScript
pulumi convert \
  --from terraform \
  --language typescript \
  --out pulumi/

# Convert to Python
pulumi convert \
  --from terraform \
  --language python \
  --out pulumi/

# Convert to Go
pulumi convert \
  --from terraform \
  --language go \
  --out pulumi/
```

Or via the Pulumi MCP server `convert` tool if configured.

## What the Converter Handles

| Terraform Construct | Pulumi Equivalent | Notes |
|---------------------|-----------------|-------|
| `resource` block | `new Provider.Resource(...)` | Direct mapping |
| `data` source | `Provider.getResourceOutput(...)` | Read-only lookup |
| `variable` | `pulumi.Config.get()` / `require()` | Set with `pulumi config set` |
| `output` | `export const name = resource.attr` | Stack exports |
| `locals` | `const` variables | Native language |
| `count` | `for` loop or array comprehension | More readable |
| `for_each` | `Object.entries(map).map(...)` | Native map operations |
| `module` | Function or class | Pulumi ComponentResource |
| `terraform_remote_state` | `pulumi.StackReference` | |
| workspace selection | Stack naming (`project/env`) | |

## Manual Cleanup After Conversion

The converter produces working code but typically needs these fixes:

### 1. Output/Input Type Cleanup

```typescript
// Generated (verbose)
const subnetIds = vpc.privateSubnetIds.apply(ids => ids);

// Simplified
const subnetIds = vpc.privateSubnetIds;
```

### 2. String Interpolation

```typescript
// Generated (may use concatenation)
const url = "https://" + lb.dnsName.apply(name => name) + "/api";

// Correct
const url = pulumi.interpolate`https://${lb.dnsName}/api`;
```

### 3. Workspace → Stack Mapping

Terraform workspaces map to Pulumi stacks:
```bash
# Terraform workspace
terraform workspace select prod

# Pulumi equivalent — init if not exists
pulumi stack init my-project/prod
pulumi stack select my-project/prod
```

### 4. Remote State → StackReference

```typescript
// Terraform
data "terraform_remote_state" "infra" {
  backend = "s3"
  config = {
    bucket = "tf-state"
    key    = "infra/terraform.tfstate"
  }
}

// Pulumi equivalent
const infraStack = new pulumi.StackReference("my-org/infra/prod");
const vpcId = infraStack.getOutput("vpcId");
```

### 5. Module → ComponentResource

```typescript
// Terraform module → Pulumi ComponentResource
export class VpcWithEndpoints extends pulumi.ComponentResource {
  public readonly vpcId: pulumi.Output<string>;
  public readonly privateSubnetIds: pulumi.Output<string[]>;

  constructor(name: string, args: VpcWithEndpointsArgs, opts?: pulumi.ComponentResourceOptions) {
    super("my-infra:vpc:VpcWithEndpoints", name, {}, opts);

    const vpc = new aws.ec2.Vpc(`${name}-vpc`, {
      cidrBlock: args.cidrBlock,
      enableDnsHostnames: true,
      tags: { Name: name },
    }, { parent: this });

    this.vpcId = vpc.id;
    // ...

    this.registerOutputs({
      vpcId: this.vpcId,
    });
  }
}
```

## Incremental Migration Strategy

Do not migrate everything at once. Use Pulumi's `import` command to take ownership of existing resources:

```bash
# Import existing Terraform-managed resource into Pulumi state
pulumi import aws:s3/bucket:Bucket my-bucket my-existing-bucket-name
```

**Strategy:**
1. Create a new Pulumi project for new resources
2. Use `pulumi.StackReference` or direct resource lookups to reference existing Terraform-managed resources
3. Migrate one module at a time: import the resources, then remove from Terraform state with `terraform state rm`
4. Validate parity with `pulumi preview` showing no changes before removing Terraform

## Import Existing Resources

```bash
# Import by resource type and cloud ID
pulumi import aws:s3/bucket:Bucket logsBucket my-existing-logs-bucket

# Import multiple resources
pulumi import \
  aws:ec2/vpc:Vpc mainVpc vpc-0abc123 \
  aws:ec2/subnet:Subnet privateSubnet subnet-0def456

# Bulk import from CSV file
pulumi import --from csv imports.csv
```

The generated code will include the resource definition matching the current state.

## State Migration

If using S3 as both Terraform and Pulumi backends, they can coexist in separate prefixes:
```
s3://my-state-bucket/
  terraform/                  # Terraform state files
  pulumi/                     # Pulumi state (set with s3://my-state-bucket?prefix=pulumi/)
```
