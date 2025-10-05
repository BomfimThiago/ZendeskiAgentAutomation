# AWS Lambda Function for TeleCorp Customer Support API
# This file defines the Lambda function and API Gateway HTTP API

# Lambda Function
resource "aws_lambda_function" "telecorp_api" {
  function_name = "${var.project_name}-customer-support"
  role          = aws_iam_role.lambda_role.arn

  # Placeholder - actual deployment done via deploy-lambda.sh script
  filename         = "lambda_placeholder.zip"
  source_code_hash = filebase64sha256("lambda_placeholder.zip")

  runtime = "python3.11"
  handler = "src.lambda_handler.lambda_handler"
  timeout = 30
  memory_size = 512

  environment {
    variables = {
      USE_BEDROCK                 = "true"
      AWS_REGION                  = var.aws_region
      DYNAMO_TABLE_CONVERSATIONS  = aws_dynamodb_table.conversations.name
      DYNAMO_TABLE_INTENT_CACHE   = aws_dynamodb_table.intent_cache.name
      DYNAMO_TABLE_SESSIONS       = aws_dynamodb_table.sessions.name
      BEDROCK_Q_LLM_MODEL         = var.bedrock_q_llm_model
      BEDROCK_P_LLM_MODEL         = var.bedrock_p_llm_model
    }
  }

  # Enable CloudWatch Logs
  logging_config {
    log_format = "JSON"
    log_group  = aws_cloudwatch_log_group.lambda_logs.name
  }

  # VPC configuration (optional - uncomment if Lambda needs VPC access)
  # vpc_config {
  #   subnet_ids         = var.private_subnet_ids
  #   security_group_ids = [aws_security_group.lambda_sg.id]
  # }

  tags = {
    Name = "${var.project_name}-lambda"
  }

  lifecycle {
    ignore_changes = [
      filename,
      source_code_hash,
      last_modified,
    ]
  }
}

# CloudWatch Log Group for Lambda
resource "aws_cloudwatch_log_group" "lambda_logs" {
  name              = "/aws/lambda/${var.project_name}-customer-support"
  retention_in_days = var.log_retention_days

  tags = {
    Name = "${var.project_name}-lambda-logs"
  }
}

# API Gateway HTTP API (v2)
resource "aws_apigatewayv2_api" "telecorp_api" {
  name          = "${var.project_name}-api"
  protocol_type = "HTTP"
  description   = "TeleCorp Customer Support API"

  cors_configuration {
    allow_origins = var.cors_origins
    allow_methods = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    allow_headers = ["*"]
    max_age       = 300
  }

  tags = {
    Name = "${var.project_name}-api-gateway"
  }
}

# API Gateway Stage (automatic deployment)
resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.telecorp_api.id
  name        = "$default"
  auto_deploy = true

  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.api_gateway_logs.arn
    format = jsonencode({
      requestId      = "$context.requestId"
      ip             = "$context.identity.sourceIp"
      requestTime    = "$context.requestTime"
      httpMethod     = "$context.httpMethod"
      routeKey       = "$context.routeKey"
      status         = "$context.status"
      protocol       = "$context.protocol"
      responseLength = "$context.responseLength"
      errorMessage   = "$context.error.message"
    })
  }

  tags = {
    Name = "${var.project_name}-api-stage"
  }
}

# CloudWatch Log Group for API Gateway
resource "aws_cloudwatch_log_group" "api_gateway_logs" {
  name              = "/aws/apigateway/${var.project_name}"
  retention_in_days = var.log_retention_days

  tags = {
    Name = "${var.project_name}-api-gateway-logs"
  }
}

# API Gateway Integration with Lambda
resource "aws_apigatewayv2_integration" "lambda_integration" {
  api_id             = aws_apigatewayv2_api.telecorp_api.id
  integration_type   = "AWS_PROXY"
  integration_method = "POST"
  integration_uri    = aws_lambda_function.telecorp_api.invoke_arn

  payload_format_version = "2.0"
  timeout_milliseconds   = 30000

  lifecycle {
    create_before_destroy = true
  }
}

# API Gateway Route (catch-all for all HTTP methods and paths)
resource "aws_apigatewayv2_route" "default_route" {
  api_id    = aws_apigatewayv2_api.telecorp_api.id
  route_key = "$default"
  target    = "integrations/${aws_apigatewayv2_integration.lambda_integration.id}"
}

# Lambda Permission to allow API Gateway to invoke
resource "aws_lambda_permission" "api_gateway_invoke" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.telecorp_api.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.telecorp_api.execution_arn}/*/*"
}

# Optional: Custom domain (uncomment and configure if needed)
# resource "aws_apigatewayv2_domain_name" "custom_domain" {
#   domain_name = var.api_domain_name
#
#   domain_name_configuration {
#     certificate_arn = var.acm_certificate_arn
#     endpoint_type   = "REGIONAL"
#     security_policy = "TLS_1_2"
#   }
# }
#
# resource "aws_apigatewayv2_api_mapping" "domain_mapping" {
#   api_id      = aws_apigatewayv2_api.telecorp_api.id
#   domain_name = aws_apigatewayv2_domain_name.custom_domain.id
#   stage       = aws_apigatewayv2_stage.default.id
# }

# Create placeholder zip file for initial deployment
resource "null_resource" "create_lambda_placeholder" {
  provisioner "local-exec" {
    command = "echo 'Placeholder' > lambda_placeholder.txt && zip lambda_placeholder.zip lambda_placeholder.txt"
  }

  triggers = {
    always_run = timestamp()
  }
}
