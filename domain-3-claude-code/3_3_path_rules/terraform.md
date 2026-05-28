---
paths: ["terraform/**/*", "infra/**/*.tf", "**/*.tfvars"]
---

# Terraform/Infrastructure Conventions (auto-loaded for IaC files)

## Module Structure
- One module per logical resource group (vpc, eks, rds)
- `main.tf`: resource definitions
- `variables.tf`: input declarations
- `outputs.tf`: exported values
- `versions.tf`: required_providers block

## Naming Conventions
- Resources: `<env>-<service>-<resource>` e.g. `prod-api-security-group`
- Variables: snake_case, descriptive names e.g. `database_instance_class`
- No hardcoded regions — always use `var.aws_region`

## Security Rules
- Never commit `.tfstate` files — always use remote state (S3 + DynamoDB lock)
- Never hardcode secrets in `.tf` or `.tfvars` — use SSM Parameter Store or Secrets Manager
- All S3 buckets must have `versioning = enabled` and `server_side_encryption_configuration`

## Change Safety
- Run `terraform plan` output must be included in PR description
- Destroying resources requires explicit comment from team lead in PR
- Production changes must go through `terraform apply` in CI, not local

## Cost Controls
- Tag all resources with: `Environment`, `Project`, `Owner`
- Use `lifecycle { prevent_destroy = true }` on stateful resources
