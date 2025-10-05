variable "aws_region" {
  description = "AWS region for all resources"
  type        = string
  default     = "us-east-1" # Best region for Bedrock (most models available)
}

variable "environment" {
  description = "Environment name (dev, staging, production)"
  type        = string
  default     = "production"
}

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
  default     = "telecorp"
}

variable "lambda_function_name" {
  description = "Name of the Lambda function"
  type        = string
  default     = "telecorp-backend"
}

variable "lambda_memory_size" {
  description = "Memory size for Lambda function in MB"
  type        = number
  default     = 512
}

variable "lambda_timeout" {
  description = "Timeout for Lambda function in seconds"
  type        = number
  default     = 30
}

variable "dynamodb_billing_mode" {
  description = "DynamoDB billing mode (PROVISIONED or PAY_PER_REQUEST)"
  type        = string
  default     = "PAY_PER_REQUEST"
}

variable "intent_cache_ttl_days" {
  description = "TTL for intent cache in days"
  type        = number
  default     = 1
}

variable "session_ttl_days" {
  description = "TTL for sessions in days"
  type        = number
  default     = 30
}

variable "bedrock_q_llm_model" {
  description = "Bedrock model ID for Q-LLM (Quarantined LLM)"
  type        = string
  default     = "anthropic.claude-3-haiku-20240307-v1:0"
}

variable "bedrock_p_llm_model" {
  description = "Bedrock model ID for P-LLM (Privileged LLM)"
  type        = string
  default     = "anthropic.claude-3-5-sonnet-20240620-v1:0"
}

variable "enable_point_in_time_recovery" {
  description = "Enable point-in-time recovery for DynamoDB tables"
  type        = bool
  default     = true
}

variable "tags" {
  description = "Additional tags for all resources"
  type        = map(string)
  default     = {}
}
