# Terraform Infrastructure

This directory would contain Terraform configuration for deploying Chatty to AWS.

## Module Structure

```
terraform/
├── main.tf                # Composes modules, wires outputs to inputs
├── variables.tf           # Top-level variables (region, environment, sizing)
├── outputs.tf             # Cluster endpoint, ALB URL, RDS endpoint
├── backend.tf             # S3 + DynamoDB for remote state and locking
│
├── environments/
│   ├── dev.tfvars         # Small node group, single-AZ RDS, spot nodes
│   ├── staging.tfvars     # Mirrors prod config at smaller scale
│   └── prod.tfvars        # Multi-AZ RDS, on-demand nodes, proper sizing
│
└── modules/
    ├── networking/        # VPC, public/private subnets, NAT gateway, security groups
    ├── eks/               # EKS cluster, managed node groups, IAM roles, OIDC provider
    ├── rds/               # RDS Postgres, subnet group, Secrets Manager for credentials
    ├── alb/               # ALB, HTTPS listener (ACM), target groups for EKS pods
    └── ecr/               # Container registry, lifecycle policies, image scanning
```

Each module is self-contained with its own `variables.tf`, `main.tf`, and `outputs.tf`. Modules are composed in the root `main.tf`. For example, the `eks` module receives `vpc_id` and `private_subnet_ids` as inputs from the `networking` module's outputs.

## Dependency Graph

```
networking ──→ eks ──→ alb
    │
    └──────→ rds

ecr (independent, can be created in parallel)
```

Networking is the foundation. VPC and subnets must exist before anything else. ECR is independent and can be provisioned in parallel. EKS depends on networking and IAM. RDS depends on networking (private subnets, security groups). ALB depends on networking (public subnets) and EKS (target groups pointing to pods).

## Key Design Decisions

- **Environment separation via tfvars**, not separate Terraform roots. Same modules, same code, different sizing and resilience per environment.
- **Private subnets** for EKS worker nodes and RDS. The database and application pods are never directly exposed to the internet. Only the ALB sits in public subnets.
- **RDS credentials** managed through AWS Secrets Manager, injected into pods via Kubernetes external-secrets-operator. No hardcoded passwords in Terraform state or environment variables.
- **EKS managed node groups** with spot instances for dev/staging (cost savings) and on-demand for production (stability). Node group sizing is controlled via tfvars.
- **OIDC provider on EKS** for IAM Roles for Service Accounts (IRSA). Pods get fine-grained AWS permissions without needing node-level IAM roles.

## Remote State Management

Terraform state is stored in S3 with DynamoDB locking:

- **S3 bucket** with versioning enabled. Allows rollback to a previous state if a bad apply corrupts it.
- **DynamoDB table** for state locking. Prevents concurrent `terraform apply` from corrupting state.
- **Bucket policy** restricts access to the CI/CD service role and a break-glass admin role only. No individual developer IAM users have write access to the state bucket.
- **Backup and recovery**. S3 versioning acts as the primary backup mechanism. If state is corrupted, you restore a previous version from the S3 version history. For additional safety, S3 cross-region replication can be enabled for the state bucket in production.

## Deployment Workflow (GitOps)

No developer runs `terraform apply` from their local machine. Infrastructure changes follow the same branching strategy as application code:

1. Developer creates a feature branch, makes Terraform changes
2. PR triggers CI which runs `terraform fmt -check` and `terraform validate`
3. CI runs `terraform plan` against the target environment and posts the plan output as a PR comment for review
4. Reviewer approves after reviewing the plan diff
5. On merge to main, CD pipeline runs `terraform apply` with the approved plan
6. For production, an additional manual approval gate is required before apply

This ensures every infrastructure change is peer-reviewed, version-controlled, and auditable.

## Terraform CI Pipeline

```yaml
# Conceptual workflow, would live in .github/workflows/terraform.yml
steps:
  - terraform fmt -check        # Formatting consistency
  - terraform validate          # Syntax and config validation
  - terraform plan              # Preview changes, post to PR
  - terraform apply             # Only on merge to main, with approved plan
```

Additional CI checks:

- **tflint** for Terraform-specific linting (deprecated syntax, naming conventions)
- **tfsec / checkov** for security scanning (open security groups, unencrypted resources, missing logging)
- **Cost estimation** via Infracost to catch unexpected spend increases before they're applied

See [RATIONALE.md](../RATIONALE.md) for the high-level reasoning behind the technology choices.