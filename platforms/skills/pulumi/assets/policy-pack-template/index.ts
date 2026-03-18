import {
  PolicyPack,
  validateResourceOfType,
  ReportViolation,
} from "@pulumi/policy";
import * as aws from "@pulumi/aws";

// ---------------------------------------------------------------------------
// Organization Policy Pack
// Customize for your organization's compliance requirements.
// ---------------------------------------------------------------------------

new PolicyPack("org-policies", {
  policies: [

    // -------------------------------------------------------------------------
    // Tagging Policy — all resources must have required tags
    // -------------------------------------------------------------------------
    {
      name: "required-tags",
      description: "All resources must have Environment, Project, and ManagedBy tags",
      enforcementLevel: "mandatory",
      validateResource: (args, reportViolation) => {
        const requiredTags = ["Environment", "Project", "ManagedBy"];
        const tags = (args.props as any)?.tags as Record<string, string> | undefined;
        if (!tags) {
          reportViolation("Resource has no tags object — all required tags are missing");
          return;
        }
        for (const tag of requiredTags) {
          if (!tags[tag]) {
            reportViolation(`Resource is missing required tag: ${tag}`);
          }
        }
      },
    },

    // -------------------------------------------------------------------------
    // S3 Security — no public access
    // -------------------------------------------------------------------------
    {
      name: "s3-no-public-access",
      description: "S3 buckets must block all public access",
      enforcementLevel: "mandatory",
      validateResource: validateResourceOfType(
        aws.s3.BucketPublicAccessBlock,
        (block, args, reportViolation) => {
          if (!block.blockPublicAcls) {
            reportViolation("S3 bucket must block public ACLs");
          }
          if (!block.blockPublicPolicy) {
            reportViolation("S3 bucket must block public bucket policies");
          }
          if (!block.ignorePublicAcls) {
            reportViolation("S3 bucket must ignore public ACLs");
          }
          if (!block.restrictPublicBuckets) {
            reportViolation("S3 bucket must restrict public buckets");
          }
        }
      ),
    },

    // -------------------------------------------------------------------------
    // S3 Versioning — must be enabled
    // -------------------------------------------------------------------------
    {
      name: "s3-versioning-required",
      description: "S3 bucket versioning must be enabled",
      enforcementLevel: "mandatory",
      validateResource: validateResourceOfType(
        aws.s3.BucketVersioningV2,
        (versioning, args, reportViolation) => {
          if (versioning.versioningConfiguration?.status !== "Enabled") {
            reportViolation("S3 bucket versioning must be Enabled");
          }
        }
      ),
    },

    // -------------------------------------------------------------------------
    // RDS — no public access
    // -------------------------------------------------------------------------
    {
      name: "rds-no-public-access",
      description: "RDS instances must not be publicly accessible",
      enforcementLevel: "mandatory",
      validateResource: validateResourceOfType(
        aws.rds.Instance,
        (instance, args, reportViolation) => {
          if (instance.publiclyAccessible) {
            reportViolation("RDS instance must not be publicly accessible");
          }
        }
      ),
    },

    // -------------------------------------------------------------------------
    // RDS — deletion protection (advisory in dev, mandatory in prod)
    // Adjust enforcementLevel per environment as needed
    // -------------------------------------------------------------------------
    {
      name: "rds-deletion-protection",
      description: "RDS instances should have deletion protection enabled",
      enforcementLevel: "advisory",
      validateResource: validateResourceOfType(
        aws.rds.Instance,
        (instance, args, reportViolation) => {
          if (!instance.deletionProtection) {
            reportViolation(
              "RDS instance should enable deletion protection to prevent accidental data loss"
            );
          }
        }
      ),
    },

    // -------------------------------------------------------------------------
    // EC2 — require approved instance types (customize the list)
    // -------------------------------------------------------------------------
    {
      name: "ec2-approved-instance-types",
      description: "EC2 instances must use approved instance types",
      enforcementLevel: "advisory",
      validateResource: validateResourceOfType(
        aws.ec2.Instance,
        (instance, args, reportViolation) => {
          const approvedTypes = [
            "t3.micro", "t3.small", "t3.medium", "t3.large",
            "m5.large", "m5.xlarge", "m5.2xlarge",
            "c5.large", "c5.xlarge",
          ];
          if (instance.instanceType && !approvedTypes.includes(instance.instanceType)) {
            reportViolation(
              `EC2 instance type "${instance.instanceType}" is not in the approved list. ` +
              `Approved types: ${approvedTypes.join(", ")}`
            );
          }
        }
      ),
    },

    // -------------------------------------------------------------------------
    // IAM — no wildcard actions or resources (advisory — too noisy for mandatory)
    // -------------------------------------------------------------------------
    {
      name: "iam-no-wildcard",
      description: "IAM policies should not use wildcard actions or resources",
      enforcementLevel: "advisory",
      validateResource: validateResourceOfType(
        aws.iam.RolePolicy,
        (policy, args, reportViolation) => {
          const doc = typeof policy.policy === "string"
            ? JSON.parse(policy.policy)
            : policy.policy;
          for (const statement of doc?.Statement ?? []) {
            const actions = Array.isArray(statement.Action) ? statement.Action : [statement.Action];
            const resources = Array.isArray(statement.Resource) ? statement.Resource : [statement.Resource];
            if (actions.includes("*") && statement.Effect === "Allow") {
              reportViolation("IAM policy has wildcard Action (*) with Allow effect");
            }
            if (resources.includes("*") && statement.Effect === "Allow" && !actions.includes("*")) {
              // Some describe/list actions legitimately require Resource: *
              const requiresWildcard = actions.every((a: string) =>
                a.startsWith("ec2:Describe") ||
                a.startsWith("ec2:List") ||
                a.startsWith("iam:List") ||
                a.startsWith("iam:GetAccount")
              );
              if (!requiresWildcard) {
                reportViolation("IAM policy has wildcard Resource (*) — scope to specific ARNs");
              }
            }
          }
        }
      ),
    },

  ],
});
