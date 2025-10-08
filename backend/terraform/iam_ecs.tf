# ECS Task Execution Role (for ECS agent - pulls images, writes logs)
resource "aws_iam_role" "ecs_execution_role" {
  name = "${var.project_name}-ecs-execution-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name        = "${var.project_name}-ecs-execution-role"
    Environment = var.environment
  }
}

# Attach AWS managed policy for ECS task execution
resource "aws_iam_role_policy_attachment" "ecs_task_execution_role" {
  role       = aws_iam_role.ecs_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# ECS Task Role (for application code - access to AWS services)
resource "aws_iam_role" "ecs_task_role" {
  name = "${var.project_name}-ecs-task-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name        = "${var.project_name}-ecs-task-role"
    Environment = var.environment
  }
}

# Policy for Bedrock access
resource "aws_iam_policy" "bedrock_access" {
  name        = "${var.project_name}-bedrock-access"
  description = "Allow ECS tasks to invoke Bedrock models"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "bedrock:InvokeModel",
          "bedrock:InvokeModelWithResponseStream"
        ]
        Resource = [
          "arn:aws:bedrock:${var.aws_region}::foundation-model/${var.bedrock_q_llm_model}",
          "arn:aws:bedrock:${var.aws_region}::foundation-model/${var.bedrock_p_llm_model}"
        ]
      }
    ]
  })

  tags = {
    Name        = "${var.project_name}-bedrock-access"
    Environment = var.environment
  }
}

# Policy for DynamoDB access
resource "aws_iam_policy" "dynamodb_access" {
  name        = "${var.project_name}-dynamodb-access"
  description = "Allow ECS tasks to access DynamoDB tables"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:DeleteItem",
          "dynamodb:Query",
          "dynamodb:Scan",
          "dynamodb:BatchGetItem",
          "dynamodb:BatchWriteItem"
        ]
        Resource = [
          aws_dynamodb_table.conversations.arn,
          aws_dynamodb_table.intent_cache.arn,
          aws_dynamodb_table.sessions.arn,
          "${aws_dynamodb_table.conversations.arn}/index/*",
          "${aws_dynamodb_table.intent_cache.arn}/index/*",
          "${aws_dynamodb_table.sessions.arn}/index/*"
        ]
      }
    ]
  })

  tags = {
    Name        = "${var.project_name}-dynamodb-access"
    Environment = var.environment
  }
}

# Attach policies to task role
resource "aws_iam_role_policy_attachment" "ecs_task_bedrock" {
  role       = aws_iam_role.ecs_task_role.name
  policy_arn = aws_iam_policy.bedrock_access.arn
}

resource "aws_iam_role_policy_attachment" "ecs_task_dynamodb" {
  role       = aws_iam_role.ecs_task_role.name
  policy_arn = aws_iam_policy.dynamodb_access.arn
}
