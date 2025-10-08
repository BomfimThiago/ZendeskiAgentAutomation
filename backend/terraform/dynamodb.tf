# DynamoDB Table: Conversations (LangGraph Checkpointer)
resource "aws_dynamodb_table" "conversations" {
  name           = "${var.project_name}-conversations"
  billing_mode   = var.dynamodb_billing_mode
  hash_key       = "session_id"
  range_key      = "checkpoint_id"

  attribute {
    name = "session_id"
    type = "S"
  }

  attribute {
    name = "checkpoint_id"
    type = "S"
  }

  # Enable point-in-time recovery for backups
  point_in_time_recovery {
    enabled = var.enable_point_in_time_recovery
  }

  # Enable encryption at rest
  server_side_encryption {
    enabled = true
  }

  # TTL for automatic cleanup
  ttl {
    attribute_name = "ttl"
    enabled        = true
  }

  tags = {
    Name        = "${var.project_name}-conversations"
    Description = "LangGraph conversation state and checkpoints with async thread pool support"
  }
}

# DynamoDB Table: Intent Cache (Q-LLM Results)
resource "aws_dynamodb_table" "intent_cache" {
  name           = "${var.project_name}-intent-cache"
  billing_mode   = var.dynamodb_billing_mode
  hash_key       = "input_hash"

  attribute {
    name = "input_hash"
    type = "S"
  }

  # Enable point-in-time recovery
  point_in_time_recovery {
    enabled = var.enable_point_in_time_recovery
  }

  # Enable encryption at rest
  server_side_encryption {
    enabled = true
  }

  # TTL for automatic cache expiration
  ttl {
    attribute_name = "ttl"
    enabled        = true
  }

  tags = {
    Name        = "${var.project_name}-intent-cache"
    Description = "Q-LLM intent extraction cache to reduce Bedrock costs"
  }
}

# DynamoDB Table: Sessions (User Session Management)
resource "aws_dynamodb_table" "sessions" {
  name           = "${var.project_name}-sessions"
  billing_mode   = var.dynamodb_billing_mode
  hash_key       = "session_id"

  attribute {
    name = "session_id"
    type = "S"
  }

  # Enable point-in-time recovery
  point_in_time_recovery {
    enabled = var.enable_point_in_time_recovery
  }

  # Enable encryption at rest
  server_side_encryption {
    enabled = true
  }

  # TTL for automatic session cleanup
  ttl {
    attribute_name = "ttl"
    enabled        = true
  }

  tags = {
    Name        = "${var.project_name}-sessions"
    Description = "User session data and metadata"
  }
}
