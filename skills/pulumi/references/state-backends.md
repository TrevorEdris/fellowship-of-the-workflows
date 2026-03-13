# Pulumi State Backends

## Backend Comparison

| Backend | Command | Locking | Secrets | Team Use | Cost |
|---------|---------|---------|---------|----------|------|
| Pulumi Cloud | default | Yes (managed) | Encrypted (Pulumi-managed) | Yes | Free tier available |
| S3 | `pulumi login s3://bucket` | Yes (DynamoDB) | Manual (KMS) | Yes | AWS costs |
| GCS | `pulumi login gs://bucket` | Yes (GCS locking) | Manual (KMS) | Yes | GCP costs |
| Azure Blob | `pulumi login azblob://container` | Yes (leases) | Manual (Key Vault) | Yes | Azure costs |
| Local | `pulumi login --local` | No | Passphrase | No | Free |

**Rule:** Never use local backend for shared or production environments. No concurrency locking means concurrent `pulumi up` runs will corrupt state.

## Pulumi Cloud (Default)

```bash
# Login to Pulumi Cloud (app.pulumi.com)
pulumi login

# Check current backend
pulumi whoami -v

# Create a stack
pulumi stack init my-org/my-project/prod
```

**Advantages:**
- Secrets encrypted by default (Pulumi-managed KMS)
- Concurrency locking built-in
- Audit log of all deployments
- Web console with history and diff view
- Team permissions and RBAC

**For self-hosted Pulumi Cloud:** `pulumi login https://pulumi.example.com`

## S3 Backend

```bash
# Create state bucket (do this once)
aws s3 mb s3://my-org-pulumi-state --region us-east-1
aws s3api put-bucket-versioning \
  --bucket my-org-pulumi-state \
  --versioning-configuration Status=Enabled

# Create DynamoDB table for locking (required for S3 backend)
aws dynamodb create-table \
  --table-name pulumi-state-lock \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST

# Login to S3 backend
pulumi login s3://my-org-pulumi-state
```

**S3 backend URL format:** `s3://<bucket>?region=<region>&endpoint=<endpoint>&awssdk=v2`

**Secrets with S3 backend:**
```bash
# Use AWS KMS for secrets encryption (recommended)
pulumi stack init my-project/prod --secrets-provider="awskms:///arn:aws:kms:us-east-1:123456789012:key/mrk-abc123"

# Or passphrase (simpler, less secure for CI)
PULUMI_CONFIG_PASSPHRASE="my-passphrase" pulumi up
```

## GCS Backend

```bash
# Create state bucket
gsutil mb gs://my-org-pulumi-state
gsutil versioning set on gs://my-org-pulumi-state

# Login
pulumi login gs://my-org-pulumi-state
```

GCS provides built-in object locking — no separate lock table needed.

**Secrets with GCS:**
```bash
pulumi stack init my-project/prod \
  --secrets-provider="gcpkms://projects/my-project/locations/global/keyRings/my-ring/cryptoKeys/my-key"
```

## Azure Blob Backend

```bash
# Create storage account and container
az storage account create \
  --name myorgpulumistate \
  --resource-group pulumi-rg \
  --sku Standard_LRS \
  --kind StorageV2

az storage container create \
  --name pulumi-state \
  --account-name myorgpulumistate

# Login
pulumi login azblob://pulumi-state?account=myorgpulumistate
```

**Secrets with Azure Blob:**
```bash
pulumi stack init my-project/prod \
  --secrets-provider="azurekeyvault://my-vault.vault.azure.net/keys/pulumi-key"
```

## State Operations

```bash
# View current backend
pulumi whoami -v

# List stacks in current backend
pulumi stack ls --all

# Export state (backup before risky operations)
pulumi stack export --file stack-backup.json

# Import state
pulumi stack import --file stack-backup.json

# Refresh state from actual cloud resources
pulumi refresh

# Move a stack to a new backend
pulumi stack export | pulumi stack import --file /dev/stdin

# Migrate from local to S3
pulumi login s3://my-bucket
pulumi stack import --file local-state-export.json
```

## CI/CD Configuration

```yaml
# GitHub Actions with Pulumi Cloud
- name: Run Pulumi
  uses: pulumi/actions@v5
  with:
    command: up
    stack-name: my-org/my-project/prod
  env:
    PULUMI_ACCESS_TOKEN: ${{ secrets.PULUMI_ACCESS_TOKEN }}
    AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
    AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}

# GitHub Actions with S3 backend
- name: Configure AWS
  uses: aws-actions/configure-aws-credentials@v4
  with:
    role-to-assume: arn:aws:iam::123456789012:role/PulumiCIRole
    aws-region: us-east-1

- name: Run Pulumi
  run: |
    pulumi login s3://my-pulumi-state
    pulumi stack select my-project/prod
    pulumi up --yes
  env:
    PULUMI_CONFIG_PASSPHRASE: ${{ secrets.PULUMI_STATE_PASSPHRASE }}
```
