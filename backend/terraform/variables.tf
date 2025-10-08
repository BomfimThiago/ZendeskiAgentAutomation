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

variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "availability_zones" {
  description = "Availability zones for subnets"
  type        = list(string)
  default     = ["us-east-1a", "us-east-1b"]
}

variable "fargate_cpu" {
  description = "Fargate CPU units (256, 512, 1024, 2048, 4096)"
  type        = string
  default     = "512"
}

variable "fargate_memory" {
  description = "Fargate memory in MB (1024, 2048, 3072, 4096, 8192, etc)"
  type        = string
  default     = "1024"
}

variable "app_count" {
  description = "Number of ECS tasks to run"
  type        = number
  default     = 1
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

variable "log_retention_days" {
  description = "CloudWatch Logs retention in days"
  type        = number
  default     = 7
}

variable "cors_origins" {
  description = "CORS allowed origins for ALB"
  type        = list(string)
  default     = ["*"]
}

variable "container_port" {
  description = "Port exposed by the Docker container"
  type        = number
  default     = 8000
}

variable "health_check_path" {
  description = "Health check endpoint path"
  type        = string
  default     = "/health"
}
