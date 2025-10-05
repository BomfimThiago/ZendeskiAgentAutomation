# TeleCorp AWS Infrastructure (Terraform)

This directory contains Terraform configuration for deploying TeleCorp backend infrastructure to AWS.

## Prerequisites

1. **Install Terraform**
   ```bash
   # macOS
   brew install terraform

   # Linux
   wget https://releases.hashicorp.com/terraform/1.6.0/terraform_1.6.0_linux_amd64.zip
   unzip terraform_1.6.0_linux_amd64.zip
   sudo mv terraform /usr/local/bin/
   ```

2. **AWS CLI Configured**
   ```bash
   aws configure
   # Your credentials are already configured for account: 724772052980
   ```

3. **Verify AWS Access**
   ```bash
   aws sts get-caller-identity
   ```

## Infrastructure Overview

This Terraform configuration creates:

- **IAM Role**: `telecorp-lambda-role` with Bedrock and DynamoDB permissions
- **DynamoDB Tables**:
  - `telecorp-conversations` - LangGraph state persistence
  - `telecorp-intent-cache` - Q-LLM intent caching (reduces costs)
  - `telecorp-sessions` - User session management
- **Policies**: Least-privilege access for Lambda to Bedrock and DynamoDB

## Cost Estimate

- **DynamoDB**: $1-5/month (on-demand pricing)
- **IAM Roles**: Free
- **Total Infrastructure**: $1-5/month
- **Runtime Costs** (Lambda + Bedrock): $20-35/month for 10k requests

## Deployment

### Step 1: Initialize Terraform

```bash
cd terraform
terraform init
```

This downloads required providers (AWS).

### Step 2: Review Plan

```bash
terraform plan
```

This shows what will be created **without** making changes.

Expected resources:
- 3 DynamoDB tables
- 1 IAM role
- 3 IAM policies
- 3 IAM role policy attachments

### Step 3: Apply Configuration

```bash
terraform apply
```

Review the plan and type `yes` to confirm.

**Estimated time**: 2-3 minutes

### Step 4: Verify Deployment

```bash
# Check DynamoDB tables
aws dynamodb list-tables --region us-east-1

# Check IAM role
aws iam get-role --role-name telecorp-lambda-role

# View outputs
terraform output
```

## Configuration

### Default Values

All defaults are set in `variables.tf`:

- **Region**: `us-east-1` (best for Bedrock)
- **Environment**: `production`
- **Billing Mode**: `PAY_PER_REQUEST` (auto-scales to zero)
- **Q-LLM Model**: Claude 3 Haiku
- **P-LLM Model**: Claude 3.5 Sonnet

### Customization

Create a `terraform.tfvars` file to override defaults:

```hcl
# terraform.tfvars
aws_region          = "us-west-2"
environment         = "staging"
lambda_memory_size  = 1024
lambda_timeout      = 60
```

## Important Notes

### 1. Bedrock Model Access

After deploying infrastructure, you **must** request Bedrock model access:

```bash
# Open AWS Console
open https://console.aws.amazon.com/bedrock

# Navigate to: Model access → Request access
# Models needed:
# - Anthropic Claude 3 Haiku
# - Anthropic Claude 3.5 Sonnet

# Approval is usually instant (1-5 minutes)
```

### 2. DynamoDB TTL

Tables have TTL enabled:
- **intent-cache**: 24 hours (configurable)
- **sessions**: 30 days (configurable)
- **conversations**: No default TTL (configure as needed)

### 3. Point-in-Time Recovery

Enabled on all tables for free backups (last 35 days).

### 4. Encryption

All tables use AWS-managed encryption at rest.

## Terraform State

### Local State (Default)

Terraform state is stored locally in `terraform.tfstate`.

**⚠️ Important**: Do NOT commit this file to Git (already in `.gitignore`).

### Remote State (Optional)

For team collaboration, use S3 backend:

```hcl
# Uncomment in main.tf
terraform {
  backend "s3" {
    bucket = "telecorp-terraform-state"
    key    = "telecorp/terraform.tfstate"
    region = "us-east-1"
  }
}
```

Create S3 bucket first:
```bash
aws s3 mb s3://telecorp-terraform-state-$(date +%s) --region us-east-1
```

## Useful Commands

```bash
# Show current state
terraform show

# List all resources
terraform state list

# Get specific output
terraform output lambda_role_arn

# Format code
terraform fmt

# Validate configuration
terraform validate

# Refresh state
terraform refresh

# Destroy all resources (⚠️ DANGER)
terraform destroy
```

## Outputs

After `terraform apply`, you'll see:

```
Outputs:

account_id = "724772052980"
region = "us-east-1"
lambda_role_arn = "arn:aws:iam::724772052980:role/telecorp-lambda-role"
dynamodb_conversations_table = {
  name = "telecorp-conversations"
  arn  = "arn:aws:dynamodb:us-east-1:724772052980:table/telecorp-conversations"
}
...
```

Use these values in your application configuration.

## Troubleshooting

### Error: AccessDenied

**Problem**: AWS credentials don't have sufficient permissions.

**Solution**: Ensure your AWS user has:
- IAM full access
- DynamoDB full access
- Or AdministratorAccess (for testing)

### Error: ResourceAlreadyExists

**Problem**: Resources already exist from previous deployment.

**Solution**:
```bash
# Import existing resources
terraform import aws_dynamodb_table.conversations telecorp-conversations

# Or destroy and recreate
terraform destroy
terraform apply
```

### Error: Bedrock models not available

**Problem**: Bedrock not available in your region.

**Solution**: Use `us-east-1` (most models) or check:
```bash
aws bedrock list-foundation-models --region us-east-1
```

## Next Steps

After successful deployment:

1. ✅ Infrastructure created
2. ⏭️ Request Bedrock model access
3. ⏭️ Phase 2: Create Bedrock integration code
4. ⏭️ Phase 3: Implement DynamoDB checkpointer
5. ⏭️ Phase 4: Deploy Lambda function

## Files

```
terraform/
├── main.tf           # Provider configuration
├── variables.tf      # Input variables
├── iam.tf           # IAM roles and policies
├── dynamodb.tf      # DynamoDB tables
├── outputs.tf       # Output values
├── .gitignore       # Ignore Terraform state files
└── README.md        # This file
```

## Security Best Practices

✅ **Implemented**:
- Least-privilege IAM policies
- Encryption at rest (DynamoDB)
- Point-in-time recovery (backups)
- TTL for automatic cleanup
- No hardcoded secrets

⚠️ **TODO**:
- Enable CloudTrail for audit logging
- Set up VPC endpoints (if using private subnet)
- Configure AWS Config for compliance
- Add budget alerts

## Cost Monitoring

Set up budget alert:

```bash
aws budgets create-budget \
  --account-id 724772052980 \
  --budget file://budget.json \
  --notifications-with-subscribers file://notifications.json
```

## Support

- **Terraform Docs**: https://registry.terraform.io/providers/hashicorp/aws/latest/docs
- **AWS Bedrock**: https://docs.aws.amazon.com/bedrock/
- **DynamoDB**: https://docs.aws.amazon.com/dynamodb/

---

**Last Updated**: 2025-10-05
**Terraform Version**: >= 1.0
**AWS Provider**: ~> 5.0
