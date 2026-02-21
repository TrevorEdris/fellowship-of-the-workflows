import * as pulumi from "@pulumi/pulumi";
import * as aws from "@pulumi/aws";

// ---------------------------------------------------------------------------
// Configuration
// ---------------------------------------------------------------------------
const config = new pulumi.Config();
const region = config.get("awsRegion") ?? "us-east-1";
const env = pulumi.getStack(); // dev | staging | prod
const project = pulumi.getProject();

// ---------------------------------------------------------------------------
// Tags applied to all resources
// ---------------------------------------------------------------------------
const commonTags: Record<string, string> = {
  Environment: env,
  Project: project,
  ManagedBy: "pulumi",
};

// ---------------------------------------------------------------------------
// Storage
// ---------------------------------------------------------------------------
const appBucket = new aws.s3.Bucket("app-data", {
  // Explicit bucket name for stable identity and drift detection
  bucket: `${project}-${env}-data`,
  tags: commonTags,
});

// Versioning (separate resource in AWS provider v6+)
const versioning = new aws.s3.BucketVersioningV2("app-data-versioning", {
  bucket: appBucket.id,
  versioningConfiguration: {
    status: "Enabled",
  },
});

// Server-side encryption
const encryption = new aws.s3.BucketServerSideEncryptionConfigurationV2("app-data-sse", {
  bucket: appBucket.id,
  rules: [{
    applyServerSideEncryptionByDefault: {
      sseAlgorithm: "AES256",
    },
  }],
});

// Block all public access
const publicAccessBlock = new aws.s3.BucketPublicAccessBlock("app-data-public-access", {
  bucket: appBucket.id,
  blockPublicAcls: true,
  blockPublicPolicy: true,
  ignorePublicAcls: true,
  restrictPublicBuckets: true,
});

// Enforce TLS via bucket policy
const bucketPolicy = new aws.s3.BucketPolicy("app-data-policy", {
  bucket: appBucket.id,
  policy: appBucket.arn.apply(arn => JSON.stringify({
    Version: "2012-10-17",
    Statement: [{
      Sid: "DenyNonTLS",
      Effect: "Deny",
      Principal: "*",
      Action: "s3:*",
      Resource: [arn, `${arn}/*`],
      Condition: {
        Bool: { "aws:SecureTransport": "false" },
      },
    }],
  })),
});

// ---------------------------------------------------------------------------
// IAM Role for application (example: Lambda)
// ---------------------------------------------------------------------------
const appRole = new aws.iam.Role("app-role", {
  name: `${project}-${env}-app`,
  assumeRolePolicy: JSON.stringify({
    Version: "2012-10-17",
    Statement: [{
      Effect: "Allow",
      Principal: { Service: "lambda.amazonaws.com" },
      Action: "sts:AssumeRole",
    }],
  }),
  tags: commonTags,
});

// Attach basic Lambda execution policy
const lambdaPolicy = new aws.iam.RolePolicyAttachment("app-role-lambda", {
  role: appRole.name,
  policyArn: "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole",
});

// Inline policy for S3 access
const s3AccessPolicy = new aws.iam.RolePolicy("app-role-s3", {
  role: appRole.id,
  policy: pulumi.all([appBucket.arn]).apply(([arn]) => JSON.stringify({
    Version: "2012-10-17",
    Statement: [{
      Effect: "Allow",
      Action: ["s3:GetObject", "s3:PutObject", "s3:DeleteObject"],
      Resource: [`${arn}/*`],
    }, {
      Effect: "Allow",
      Action: ["s3:ListBucket"],
      Resource: [arn],
    }],
  })),
});

// ---------------------------------------------------------------------------
// Exports — visible via `pulumi stack output`
// ---------------------------------------------------------------------------
export const bucketName = appBucket.id;
export const bucketArn = appBucket.arn;
export const appRoleArn = appRole.arn;
