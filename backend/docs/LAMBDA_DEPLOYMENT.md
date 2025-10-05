# Lambda Deployment Guide

Complete guide for deploying TeleCorp Customer Support API to AWS Lambda.

## Architecture Overview

```
User Request
    ↓
API Gateway (HTTP API)
    ↓
Lambda Function (FastAPI + Mangum)
    ↓
├─ Bedrock (Claude 3 Haiku + Sonnet)
├─ DynamoDB (State + Cache)
└─ CloudWatch Logs
```

## Prerequisites

1. **AWS Infrastructure Deployed**
   ```bash
   cd terraform
   terraform init
   terraform apply
   ```

2. **Bedrock Model Access Requested**
   - Go to: https://console.aws.amazon.com/bedrock/home?region=us-east-1#/modelaccess
   - Request access to:
     - Anthropic Claude 3 Haiku
     - Anthropic Claude 3.5 Sonnet

3. **AWS CLI Configured**
   ```bash
   aws configure
   # Or use existing profile
   export AWS_PROFILE=your-profile
   ```

4. **Python 3.11+ Installed**
   ```bash
   python --version  # Should be 3.11 or higher
   ```

## Deployment Steps

### Option 1: Automated Deployment (Recommended)

Run the deployment script:

```bash
cd backend
./scripts/deploy-lambda.sh
```

This script will:
1. Clean previous deployment artifacts
2. Install Lambda dependencies (Linux-compatible)
3. Package application code
4. Create deployment ZIP (optimize size)
5. Upload to Lambda
6. Configure environment variables
7. Set up IAM permissions

### Option 2: Manual Deployment

If you need more control, follow these manual steps:

#### Step 1: Create Deployment Package

```bash
cd backend

# Create deployment directory
mkdir -p lambda_deployment
cd lambda_deployment

# Install dependencies for Lambda (Linux x86_64)
pip install \
    --target . \
    --platform manylinux2014_x86_64 \
    --only-binary=:all: \
    --python-version 3.11 \
    -r ../requirements/lambda.txt

# Copy application code
cp -r ../src .

# Clean up (reduce package size)
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -name "*.pyc" -delete
rm -rf boto3 botocore  # Provided by Lambda runtime

# Create ZIP
zip -r ../lambda_function.zip . -q
cd ..
```

#### Step 2: Deploy to Lambda

```bash
# Update function code
aws lambda update-function-code \
    --function-name telecorp-customer-support \
    --zip-file fileb://lambda_function.zip \
    --region us-east-1

# Wait for update to complete
aws lambda wait function-updated \
    --function-name telecorp-customer-support \
    --region us-east-1

# Update function configuration
aws lambda update-function-configuration \
    --function-name telecorp-customer-support \
    --runtime python3.11 \
    --handler src.lambda_handler.lambda_handler \
    --timeout 30 \
    --memory-size 512 \
    --environment "Variables={
        USE_BEDROCK=true,
        AWS_REGION=us-east-1,
        DYNAMO_TABLE_CONVERSATIONS=telecorp-conversations,
        DYNAMO_TABLE_INTENT_CACHE=telecorp-intent-cache,
        DYNAMO_TABLE_SESSIONS=telecorp-sessions,
        BEDROCK_Q_LLM_MODEL=anthropic.claude-3-haiku-20240307-v1:0,
        BEDROCK_P_LLM_MODEL=anthropic.claude-3-5-sonnet-20240620-v1:0
    }" \
    --region us-east-1
```

## Testing

### 1. Health Check

```bash
# Get API Gateway URL
API_URL=$(cd terraform && terraform output -raw api_gateway_url)

# Test health endpoint
curl $API_URL/health
```

Expected response:
```json
{"status": "healthy"}
```

### 2. Invoke Lambda Directly

```bash
# Create test event
cat > test_event.json <<EOF
{
  "requestContext": {
    "http": {
      "method": "GET",
      "path": "/health"
    }
  },
  "rawPath": "/health",
  "headers": {}
}
EOF

# Invoke function
aws lambda invoke \
    --function-name telecorp-customer-support \
    --payload file://test_event.json \
    --region us-east-1 \
    response.json

# View response
cat response.json | jq .
```

### 3. Test API Endpoints

```bash
# Test conversation endpoint
curl -X POST $API_URL/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello, I need help with my internet",
    "session_id": "test-session-123"
  }'
```

## Monitoring

### CloudWatch Logs

**View Lambda Logs:**
```bash
aws logs tail /aws/lambda/telecorp-customer-support --follow
```

**View API Gateway Logs:**
```bash
aws logs tail /aws/apigateway/telecorp --follow
```

### Metrics

**Lambda Metrics:**
- Invocations
- Duration
- Error count
- Throttles
- Cold starts

**API Gateway Metrics:**
- Request count
- 4XX errors
- 5XX errors
- Latency

View in CloudWatch Console:
https://console.aws.amazon.com/cloudwatch/home?region=us-east-1

## Troubleshooting

### Issue: "Operation not allowed" from Bedrock

**Cause:** Bedrock model access not granted

**Solution:**
1. Go to: https://console.aws.amazon.com/bedrock/home?region=us-east-1#/modelaccess
2. Click "Manage model access"
3. Select Claude 3 Haiku and Claude 3.5 Sonnet
4. Click "Request model access"
5. Wait for approval (usually instant for Claude models)

### Issue: Lambda package too large (>50MB compressed)

**Cause:** Dependencies exceed Lambda limit

**Solutions:**
1. **Use Lambda Layers:**
   ```bash
   # Create layer for heavy dependencies
   pip install -t python/lib/python3.11/site-packages langchain langgraph
   zip -r layer.zip python/
   aws lambda publish-layer-version --layer-name telecorp-deps --zip-file fileb://layer.zip
   ```

2. **Exclude unnecessary files:**
   - Remove test directories
   - Remove .dist-info directories
   - Remove boto3/botocore (provided by Lambda)

3. **Use external storage:**
   - Store large models in S3
   - Download on Lambda cold start

### Issue: "Task timed out after 30.00 seconds"

**Cause:** Function timeout too low

**Solution:**
```bash
aws lambda update-function-configuration \
    --function-name telecorp-customer-support \
    --timeout 60 \
    --region us-east-1
```

### Issue: Cold start latency (>5 seconds)

**Causes:**
- Large deployment package
- Heavy imports
- Cold Lambda container

**Solutions:**
1. **Use Provisioned Concurrency:**
   ```bash
   aws lambda put-provisioned-concurrency-config \
       --function-name telecorp-customer-support \
       --provisioned-concurrent-executions 1 \
       --region us-east-1
   ```
   Note: Costs ~$13/month per provisioned instance

2. **Optimize imports:**
   - Lazy import heavy modules
   - Move imports inside functions

3. **Use Lambda SnapStart** (Java only, not for Python)

### Issue: DynamoDB access denied

**Cause:** Lambda role missing DynamoDB permissions

**Solution:**
```bash
cd terraform
terraform apply  # Re-apply IAM policies
```

## Cost Optimization

### Current Configuration
- Lambda: 512MB memory, 30s timeout
- API Gateway: HTTP API (cheaper than REST API)
- DynamoDB: Pay-per-request (no provisioned capacity)
- CloudWatch: 7-day retention

### Estimated Costs (10k requests/month)
- Lambda: ~$2.50/month
- API Gateway: ~$1.00/month
- DynamoDB: ~$1.50/month
- Bedrock:
  - Haiku (Q-LLM): ~$5/month (with 35% cache hit rate)
  - Sonnet (P-LLM): ~$15/month
- CloudWatch Logs: ~$0.50/month

**Total: ~$25-30/month**

### Cost Optimization Tips

1. **Enable intent caching** (already implemented)
   - 30-40% reduction in Q-LLM calls
   - ~$3.50/month savings

2. **Reduce Lambda memory** (if performance allows)
   ```bash
   aws lambda update-function-configuration \
       --function-name telecorp-customer-support \
       --memory-size 256 \
       --region us-east-1
   ```

3. **Adjust log retention**
   ```bash
   aws logs put-retention-policy \
       --log-group-name /aws/lambda/telecorp-customer-support \
       --retention-in-days 3 \
       --region us-east-1
   ```

4. **Monitor unused DynamoDB capacity**
   - Use pay-per-request (already configured)
   - Enable DynamoDB auto-scaling if switching to provisioned

## Deployment Checklist

- [ ] Terraform infrastructure deployed
- [ ] Bedrock model access granted
- [ ] Lambda function deployed
- [ ] API Gateway configured
- [ ] Environment variables set
- [ ] Health check passes
- [ ] CloudWatch Logs working
- [ ] DynamoDB tables accessible
- [ ] Intent caching working
- [ ] End-to-end conversation test passes

## Next Steps

1. **Deploy Frontend:**
   - Build React app
   - Upload to S3
   - Configure CloudFront CDN
   - Point to API Gateway URL

2. **Production Hardening:**
   - Add custom domain (Route 53 + ACM)
   - Enable API Gateway throttling
   - Set up CloudWatch alarms
   - Configure backup policies
   - Implement CI/CD pipeline

3. **Monitoring & Observability:**
   - Set up X-Ray tracing
   - Configure custom metrics
   - Create CloudWatch dashboards
   - Set up SNS alerts

## Support

For issues or questions:
- Check CloudWatch Logs
- Review Terraform outputs
- Consult AWS documentation
- Open GitHub issue
