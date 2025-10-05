#!/bin/bash

# TeleCorp Lambda Deployment Script
# This script packages and deploys the FastAPI application to AWS Lambda

set -e  # Exit on error

# Configuration
FUNCTION_NAME="telecorp-customer-support"
REGION="${AWS_REGION:-us-east-1}"
RUNTIME="python3.11"
HANDLER="src.lambda_handler.lambda_handler"
DEPLOYMENT_DIR="lambda_deployment"
ZIP_FILE="lambda_function.zip"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 TeleCorp Lambda Deployment${NC}"
echo "=================================="
echo "Function: $FUNCTION_NAME"
echo "Region: $REGION"
echo "Runtime: $RUNTIME"
echo ""

# Step 1: Clean previous deployment artifacts
echo -e "${YELLOW}📦 Step 1: Cleaning previous deployment artifacts${NC}"
if [ -d "$DEPLOYMENT_DIR" ]; then
    rm -rf "$DEPLOYMENT_DIR"
    echo "✓ Removed old deployment directory"
fi
if [ -f "$ZIP_FILE" ]; then
    rm "$ZIP_FILE"
    echo "✓ Removed old deployment package"
fi

# Step 2: Create deployment directory
echo -e "${YELLOW}📁 Step 2: Creating deployment directory${NC}"
mkdir -p "$DEPLOYMENT_DIR"
echo "✓ Created $DEPLOYMENT_DIR"

# Step 3: Install Lambda dependencies
echo -e "${YELLOW}📚 Step 3: Installing Lambda dependencies${NC}"
echo "This may take a few minutes..."

# Install dependencies to deployment directory
# Use --platform to ensure Linux compatibility
pip install \
    --target "$DEPLOYMENT_DIR" \
    --platform manylinux2014_x86_64 \
    --only-binary=:all: \
    --python-version 3.11 \
    --implementation cp \
    -r requirements/lambda.txt

echo "✓ Dependencies installed"

# Step 4: Copy application code
echo -e "${YELLOW}📄 Step 4: Copying application code${NC}"
cp -r src "$DEPLOYMENT_DIR/"
echo "✓ Application code copied"

# Step 5: Copy configuration files
echo -e "${YELLOW}⚙️  Step 5: Copying configuration files${NC}"
# Note: .env is NOT copied for security (use Lambda environment variables)
# Copy any other config files if needed
echo "✓ Configuration files handled"

# Step 6: Clean up unnecessary files (reduce package size)
echo -e "${YELLOW}🧹 Step 6: Cleaning up unnecessary files${NC}"
cd "$DEPLOYMENT_DIR"

# Remove test files
find . -type d -name "tests" -exec rm -rf {} + 2>/dev/null || true
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -name "*.pyc" -delete 2>/dev/null || true
find . -name "*.pyo" -delete 2>/dev/null || true
find . -name "*.dist-info" -exec rm -rf {} + 2>/dev/null || true

# Remove heavy/unnecessary packages
rm -rf \
    boto3 \
    botocore \
    awscli \
    pip \
    setuptools \
    wheel \
    2>/dev/null || true

echo "✓ Unnecessary files removed"

# Step 7: Create deployment package
echo -e "${YELLOW}📦 Step 7: Creating deployment package${NC}"
zip -r "../$ZIP_FILE" . -q
cd ..
echo "✓ Deployment package created: $ZIP_FILE"

# Check package size
PACKAGE_SIZE=$(du -h "$ZIP_FILE" | cut -f1)
echo "Package size: $PACKAGE_SIZE"

# Step 8: Check if Lambda function exists
echo -e "${YELLOW}🔍 Step 8: Checking if Lambda function exists${NC}"
if aws lambda get-function --function-name "$FUNCTION_NAME" --region "$REGION" &>/dev/null; then
    echo "✓ Function exists, will update"
    FUNCTION_EXISTS=true
else
    echo "✓ Function does not exist, will create"
    FUNCTION_EXISTS=false
fi

# Step 9: Get IAM role ARN from Terraform output
echo -e "${YELLOW}🔑 Step 9: Getting IAM role ARN${NC}"
cd terraform
ROLE_ARN=$(terraform output -raw lambda_role_arn 2>/dev/null || echo "")
cd ..

if [ -z "$ROLE_ARN" ]; then
    echo -e "${RED}❌ Error: Could not get Lambda role ARN from Terraform${NC}"
    echo "Please run 'terraform apply' in the terraform directory first"
    exit 1
fi
echo "✓ IAM Role ARN: $ROLE_ARN"

# Step 10: Deploy to Lambda
echo -e "${YELLOW}☁️  Step 10: Deploying to AWS Lambda${NC}"

if [ "$FUNCTION_EXISTS" = true ]; then
    # Update existing function
    echo "Updating function code..."
    aws lambda update-function-code \
        --function-name "$FUNCTION_NAME" \
        --zip-file "fileb://$ZIP_FILE" \
        --region "$REGION" \
        --no-cli-pager

    echo "Waiting for function update to complete..."
    aws lambda wait function-updated \
        --function-name "$FUNCTION_NAME" \
        --region "$REGION"

    echo "Updating function configuration..."
    aws lambda update-function-configuration \
        --function-name "$FUNCTION_NAME" \
        --runtime "$RUNTIME" \
        --handler "$HANDLER" \
        --timeout 30 \
        --memory-size 512 \
        --region "$REGION" \
        --no-cli-pager

    echo "✓ Function updated successfully"
else
    # Create new function
    echo "Creating new Lambda function..."
    aws lambda create-function \
        --function-name "$FUNCTION_NAME" \
        --runtime "$RUNTIME" \
        --role "$ROLE_ARN" \
        --handler "$HANDLER" \
        --zip-file "fileb://$ZIP_FILE" \
        --timeout 30 \
        --memory-size 512 \
        --region "$REGION" \
        --no-cli-pager

    echo "✓ Function created successfully"
fi

# Step 11: Set environment variables
echo -e "${YELLOW}🔧 Step 11: Setting environment variables${NC}"
aws lambda update-function-configuration \
    --function-name "$FUNCTION_NAME" \
    --environment "Variables={
        USE_BEDROCK=true,
        AWS_REGION=$REGION,
        DYNAMO_TABLE_CONVERSATIONS=telecorp-conversations,
        DYNAMO_TABLE_INTENT_CACHE=telecorp-intent-cache,
        DYNAMO_TABLE_SESSIONS=telecorp-sessions,
        BEDROCK_Q_LLM_MODEL=anthropic.claude-3-haiku-20240307-v1:0,
        BEDROCK_P_LLM_MODEL=anthropic.claude-3-5-sonnet-20240620-v1:0
    }" \
    --region "$REGION" \
    --no-cli-pager

echo "✓ Environment variables configured"

# Step 12: Get function URL
echo -e "${YELLOW}🌐 Step 12: Getting function details${NC}"
FUNCTION_ARN=$(aws lambda get-function \
    --function-name "$FUNCTION_NAME" \
    --region "$REGION" \
    --query 'Configuration.FunctionArn' \
    --output text)

echo "✓ Function ARN: $FUNCTION_ARN"

# Step 13: Clean up local deployment artifacts (optional)
echo -e "${YELLOW}🧹 Step 13: Cleaning up local deployment artifacts${NC}"
echo "Keep deployment artifacts? (y/n)"
read -r KEEP_ARTIFACTS

if [ "$KEEP_ARTIFACTS" != "y" ]; then
    rm -rf "$DEPLOYMENT_DIR"
    rm "$ZIP_FILE"
    echo "✓ Local deployment artifacts removed"
else
    echo "✓ Deployment artifacts kept for inspection"
fi

# Done!
echo ""
echo -e "${GREEN}✅ Deployment Complete!${NC}"
echo "=================================="
echo "Function Name: $FUNCTION_NAME"
echo "Function ARN: $FUNCTION_ARN"
echo "Region: $REGION"
echo ""
echo "Next steps:"
echo "1. Create API Gateway HTTP API (or use Terraform)"
echo "2. Test the function with sample events"
echo "3. Monitor CloudWatch Logs for any issues"
echo ""
echo "Test the function:"
echo "  aws lambda invoke --function-name $FUNCTION_NAME --region $REGION response.json"
