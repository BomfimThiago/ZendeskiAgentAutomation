output "account_id" {
  description = "AWS Account ID"
  value       = data.aws_caller_identity.current.account_id
}

output "region" {
  description = "AWS Region"
  value       = data.aws_region.current.name
}

output "lambda_role_arn" {
  description = "ARN of the Lambda execution role"
  value       = aws_iam_role.lambda_role.arn
}

output "lambda_role_name" {
  description = "Name of the Lambda execution role"
  value       = aws_iam_role.lambda_role.name
}

output "dynamodb_conversations_table" {
  description = "DynamoDB conversations table details"
  value = {
    name = aws_dynamodb_table.conversations.name
    arn  = aws_dynamodb_table.conversations.arn
  }
}

output "dynamodb_intent_cache_table" {
  description = "DynamoDB intent cache table details"
  value = {
    name = aws_dynamodb_table.intent_cache.name
    arn  = aws_dynamodb_table.intent_cache.arn
  }
}

output "dynamodb_sessions_table" {
  description = "DynamoDB sessions table details"
  value = {
    name = aws_dynamodb_table.sessions.name
    arn  = aws_dynamodb_table.sessions.arn
  }
}

output "bedrock_models" {
  description = "Bedrock model IDs configured"
  value = {
    q_llm = var.bedrock_q_llm_model
    p_llm = var.bedrock_p_llm_model
  }
}

output "environment_variables" {
  description = "Environment variables for Lambda function"
  value = {
    USE_BEDROCK                   = "true"
    AWS_REGION                    = var.aws_region
    BEDROCK_Q_LLM_MODEL           = var.bedrock_q_llm_model
    BEDROCK_P_LLM_MODEL           = var.bedrock_p_llm_model
    DYNAMO_TABLE_CONVERSATIONS    = aws_dynamodb_table.conversations.name
    DYNAMO_TABLE_INTENT_CACHE     = aws_dynamodb_table.intent_cache.name
    DYNAMO_TABLE_SESSIONS         = aws_dynamodb_table.sessions.name
  }
}

output "next_steps" {
  description = "Next steps after Terraform deployment"
  value = <<-EOT

  ✅ Infrastructure deployed successfully!

  📋 Next Steps:
  1. Request Bedrock model access:
     - Go to: https://console.aws.amazon.com/bedrock
     - Navigate to: Model access
     - Request access to:
       • Anthropic Claude 3 Haiku
       • Anthropic Claude 3.5 Sonnet

  2. Verify Bedrock access:
     aws bedrock list-foundation-models --region ${var.aws_region} | grep claude

  3. Continue to Phase 2: Bedrock Integration
     - Create BedrockChatModel wrapper
     - Update agent nodes

  4. Test the infrastructure:
     - Run unit tests
     - Deploy Lambda function

  💰 Estimated Monthly Cost: $25-40 (for 10k requests)

  EOT
}
