output "account_id" {
  description = "AWS Account ID"
  value       = data.aws_caller_identity.current.account_id
}

output "region" {
  description = "AWS Region"
  value       = data.aws_region.current.name
}

# ECS Outputs
output "ecs_cluster_name" {
  description = "ECS cluster name"
  value       = aws_ecs_cluster.main.name
}

output "ecs_service_name" {
  description = "ECS service name"
  value       = aws_ecs_service.main.name
}

output "ecs_task_role_arn" {
  description = "ARN of the ECS task role"
  value       = aws_iam_role.ecs_task_role.arn
}

output "ecs_execution_role_arn" {
  description = "ARN of the ECS execution role"
  value       = aws_iam_role.ecs_execution_role.arn
}

# ECR Outputs
output "ecr_repository_url" {
  description = "ECR repository URL"
  value       = aws_ecr_repository.telecorp_api.repository_url
}

output "ecr_repository_name" {
  description = "ECR repository name"
  value       = aws_ecr_repository.telecorp_api.name
}

# ALB Outputs
output "alb_dns_name" {
  description = "DNS name of the load balancer"
  value       = aws_lb.main.dns_name
}

output "alb_url" {
  description = "Load Balancer URL"
  value       = "http://${aws_lb.main.dns_name}"
}

output "alb_zone_id" {
  description = "Zone ID of the load balancer"
  value       = aws_lb.main.zone_id
}

# DynamoDB Outputs
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

# Bedrock Outputs
output "bedrock_models" {
  description = "Bedrock model IDs configured"
  value = {
    q_llm = var.bedrock_q_llm_model
    p_llm = var.bedrock_p_llm_model
  }
}

# Environment Variables
output "environment_variables" {
  description = "Environment variables for ECS tasks"
  value = {
    USE_BEDROCK                = "true"
    BEDROCK_Q_LLM_MODEL        = var.bedrock_q_llm_model
    BEDROCK_P_LLM_MODEL        = var.bedrock_p_llm_model
    DYNAMO_TABLE_CONVERSATIONS = aws_dynamodb_table.conversations.name
    DYNAMO_TABLE_INTENT_CACHE  = aws_dynamodb_table.intent_cache.name
    DYNAMO_TABLE_SESSIONS      = aws_dynamodb_table.sessions.name
  }
}

# Networking Outputs
output "vpc_id" {
  description = "VPC ID"
  value       = aws_vpc.main.id
}

output "public_subnet_ids" {
  description = "Public subnet IDs"
  value       = aws_subnet.public[*].id
}

output "private_subnet_ids" {
  description = "Private subnet IDs"
  value       = aws_subnet.private[*].id
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

  2. Build and Push Docker Image:
     cd backend
     aws ecr get-login-password --region ${var.aws_region} | docker login --username AWS --password-stdin ${aws_ecr_repository.telecorp_api.repository_url}
     docker build -t ${aws_ecr_repository.telecorp_api.name} .
     docker tag ${aws_ecr_repository.telecorp_api.name}:latest ${aws_ecr_repository.telecorp_api.repository_url}:latest
     docker push ${aws_ecr_repository.telecorp_api.repository_url}:latest

  3. Test API:
     curl http://${aws_lb.main.dns_name}/health
     curl http://${aws_lb.main.dns_name}/docs

  🌐 API Endpoints:
     Base URL: http://${aws_lb.main.dns_name}
     Health:   http://${aws_lb.main.dns_name}/health
     API Docs: http://${aws_lb.main.dns_name}/docs

  📊 Monitor Logs:
     ECS Logs: aws logs tail /ecs/${var.project_name} --follow

  💰 Estimated Monthly Cost: $25-50 (1 Fargate task + ALB + DynamoDB)

  EOT
}
