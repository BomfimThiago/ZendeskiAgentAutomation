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

# Lambda Function Outputs
output "lambda_function_name" {
  description = "Lambda function name"
  value       = aws_lambda_function.telecorp_api.function_name
}

output "lambda_function_arn" {
  description = "Lambda function ARN"
  value       = aws_lambda_function.telecorp_api.arn
}

output "lambda_role_arn" {
  description = "Lambda IAM role ARN"
  value       = aws_iam_role.lambda_role.arn
}

# API Gateway Outputs
output "api_gateway_url" {
  description = "API Gateway invoke URL"
  value       = aws_apigatewayv2_stage.default.invoke_url
}

output "api_gateway_id" {
  description = "API Gateway ID"
  value       = aws_apigatewayv2_api.telecorp_api.id
}

output "next_steps" {
  description = "Next steps after Terraform deployment"
  value = <<-EOT

  ✅ Infrastructure deployed successfully!

  📋 Deployment Steps:

  1. Request Bedrock model access:
     https://console.aws.amazon.com/bedrock/home?region=${var.aws_region}#/modelaccess
     - Enable: Claude 3 Haiku
     - Enable: Claude 3.5 Sonnet

  2. Deploy Lambda Function:
     cd backend
     ./scripts/deploy-lambda.sh

  3. Test API:
     curl ${aws_apigatewayv2_stage.default.invoke_url}/health

  🌐 API Endpoints:
     Base URL: ${aws_apigatewayv2_stage.default.invoke_url}
     Health:   ${aws_apigatewayv2_stage.default.invoke_url}/health
     API Docs: ${aws_apigatewayv2_stage.default.invoke_url}/docs

  📊 Monitor Logs:
     Lambda:      aws logs tail /aws/lambda/${aws_lambda_function.telecorp_api.function_name} --follow
     API Gateway: aws logs tail /aws/apigateway/${var.project_name} --follow

  💰 Estimated Monthly Cost: $25-40 (for 10k requests)

  EOT
}
