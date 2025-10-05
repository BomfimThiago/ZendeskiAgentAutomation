#!/bin/bash

set -e  # Exit on error

echo "🚀 Phase 1: AWS Account Setup"
echo "================================"
echo ""

# Configuration
REGION="us-east-1"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

echo "📋 Account Information:"
echo "  Account ID: $ACCOUNT_ID"
echo "  Region: $REGION"
echo ""

# Step 1: Check Bedrock Model Access
echo "📝 Step 1: Checking Bedrock model access..."
echo ""

# Check if we can list Bedrock models
if aws bedrock list-foundation-models --region $REGION &> /dev/null; then
    echo "✅ Bedrock API access working"

    # Check for Claude models
    echo ""
    echo "Available Claude models:"
    aws bedrock list-foundation-models --region $REGION \
        --query 'modelSummaries[?contains(modelId, `claude`)].{ModelId:modelId,Name:modelName}' \
        --output table

    echo ""
    echo "⚠️  IMPORTANT: You need to request access to Claude models"
    echo "   1. Go to: https://console.aws.amazon.com/bedrock"
    echo "   2. Click 'Model access' in the left menu"
    echo "   3. Request access to:"
    echo "      - Anthropic Claude 3 Haiku"
    echo "      - Anthropic Claude 3.5 Sonnet"
    echo "   4. Approval is usually instant"
    echo ""
    read -p "Press Enter once you've requested access..."
else
    echo "❌ Cannot access Bedrock API"
    echo "   Make sure you're in a region that supports Bedrock (us-east-1)"
    exit 1
fi

# Step 2: Create IAM Role for Lambda
echo ""
echo "📝 Step 2: Creating IAM role for Lambda..."
echo ""

ROLE_NAME="TeleCorpLambdaRole"

# Check if role already exists
if aws iam get-role --role-name $ROLE_NAME &> /dev/null; then
    echo "⚠️  Role '$ROLE_NAME' already exists, skipping creation"
else
    # Create trust policy
    cat > /tmp/lambda-trust-policy.json <<'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

    # Create role
    aws iam create-role \
        --role-name $ROLE_NAME \
        --assume-role-policy-document file:///tmp/lambda-trust-policy.json \
        --description "Role for TeleCorp Lambda function with Bedrock and DynamoDB access"

    echo "✅ Created IAM role: $ROLE_NAME"
fi

# Attach basic Lambda execution policy
echo "   Attaching basic execution policy..."
aws iam attach-role-policy \
    --role-name $ROLE_NAME \
    --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole \
    2>/dev/null || echo "   Policy already attached"

# Create custom policy for Bedrock + DynamoDB
echo "   Creating custom policy for Bedrock and DynamoDB..."

cat > /tmp/telecorp-lambda-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "BedrockAccess",
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock:InvokeModelWithResponseStream"
      ],
      "Resource": [
        "arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-haiku-20240307-v1:0",
        "arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-5-sonnet-20240620-v1:0"
      ]
    },
    {
      "Sid": "DynamoDBAccess",
      "Effect": "Allow",
      "Action": [
        "dynamodb:PutItem",
        "dynamodb:GetItem",
        "dynamodb:UpdateItem",
        "dynamodb:Query",
        "dynamodb:Scan",
        "dynamodb:DeleteItem",
        "dynamodb:BatchGetItem",
        "dynamodb:BatchWriteItem"
      ],
      "Resource": [
        "arn:aws:dynamodb:us-east-1:$ACCOUNT_ID:table/telecorp-*"
      ]
    },
    {
      "Sid": "CloudWatchLogs",
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:us-east-1:$ACCOUNT_ID:*"
    }
  ]
}
EOF

aws iam put-role-policy \
    --role-name $ROLE_NAME \
    --policy-name TeleCorpLambdaPolicy \
    --policy-document file:///tmp/telecorp-lambda-policy.json

echo "✅ Created and attached custom policy"

# Step 3: Create DynamoDB Tables
echo ""
echo "📝 Step 3: Creating DynamoDB tables..."
echo ""

# Table 1: Conversations (LangGraph state)
TABLE_NAME="telecorp-conversations"
if aws dynamodb describe-table --table-name $TABLE_NAME --region $REGION &> /dev/null; then
    echo "⚠️  Table '$TABLE_NAME' already exists, skipping"
else
    echo "   Creating $TABLE_NAME..."
    aws dynamodb create-table \
        --table-name $TABLE_NAME \
        --attribute-definitions \
            AttributeName=session_id,AttributeType=S \
            AttributeName=checkpoint_id,AttributeType=S \
        --key-schema \
            AttributeName=session_id,KeyType=HASH \
            AttributeName=checkpoint_id,KeyType=RANGE \
        --billing-mode PAY_PER_REQUEST \
        --region $REGION \
        --tags Key=Project,Value=TeleCorp Key=Environment,Value=Production

    echo "✅ Created table: $TABLE_NAME"
fi

# Table 2: Intent Cache
TABLE_NAME="telecorp-intent-cache"
if aws dynamodb describe-table --table-name $TABLE_NAME --region $REGION &> /dev/null; then
    echo "⚠️  Table '$TABLE_NAME' already exists, skipping"
else
    echo "   Creating $TABLE_NAME..."
    aws dynamodb create-table \
        --table-name $TABLE_NAME \
        --attribute-definitions \
            AttributeName=input_hash,AttributeType=S \
        --key-schema \
            AttributeName=input_hash,KeyType=HASH \
        --billing-mode PAY_PER_REQUEST \
        --region $REGION \
        --tags Key=Project,Value=TeleCorp Key=Environment,Value=Production

    echo "✅ Created table: $TABLE_NAME"

    # Enable TTL
    echo "   Enabling TTL on $TABLE_NAME..."
    aws dynamodb update-time-to-live \
        --table-name $TABLE_NAME \
        --time-to-live-specification Enabled=true,AttributeName=ttl \
        --region $REGION
fi

# Table 3: Sessions
TABLE_NAME="telecorp-sessions"
if aws dynamodb describe-table --table-name $TABLE_NAME --region $REGION &> /dev/null; then
    echo "⚠️  Table '$TABLE_NAME' already exists, skipping"
else
    echo "   Creating $TABLE_NAME..."
    aws dynamodb create-table \
        --table-name $TABLE_NAME \
        --attribute-definitions \
            AttributeName=session_id,AttributeType=S \
        --key-schema \
            AttributeName=session_id,KeyType=HASH \
        --billing-mode PAY_PER_REQUEST \
        --region $REGION \
        --tags Key=Project,Value=TeleCorp Key=Environment,Value=Production

    echo "✅ Created table: $TABLE_NAME"

    # Enable TTL
    echo "   Enabling TTL on $TABLE_NAME..."
    aws dynamodb update-time-to-live \
        --table-name $TABLE_NAME \
        --time-to-live-specification Enabled=true,AttributeName=ttl \
        --region $REGION
fi

# Summary
echo ""
echo "================================"
echo "✅ Phase 1 Setup Complete!"
echo "================================"
echo ""
echo "📊 Created Resources:"
echo "  - IAM Role: TeleCorpLambdaRole"
echo "  - DynamoDB Tables:"
echo "    • telecorp-conversations (LangGraph state)"
echo "    • telecorp-intent-cache (Q-LLM caching)"
echo "    • telecorp-sessions (user sessions)"
echo ""
echo "📋 Next Steps:"
echo "  1. Verify Bedrock model access is approved"
echo "  2. Run: ./scripts/verify-phase1.sh"
echo "  3. Proceed to Phase 2: Bedrock Integration"
echo ""

# Save configuration
cat > /tmp/telecorp-config.txt <<EOF
ACCOUNT_ID=$ACCOUNT_ID
REGION=$REGION
ROLE_NAME=$ROLE_NAME
ROLE_ARN=arn:aws:iam::$ACCOUNT_ID:role/$ROLE_NAME
EOF

echo "💾 Configuration saved to: /tmp/telecorp-config.txt"
