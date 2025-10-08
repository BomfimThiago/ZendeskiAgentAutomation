#!/bin/bash

# AWS ECS Deployment Script for MyAwesomeFakeCompany Backend
# This script builds and deploys the Docker container to AWS ECS

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration
AWS_REGION="us-east-1"
AWS_ACCOUNT_ID="724772052980"
ECR_REPOSITORY="myawesomefakecompany-api"
IMAGE_NAME="myawesomefakecompany-backend"
ECS_CLUSTER="telecorp-cluster"
ECS_SERVICE="telecorp-service"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}MyAwesomeFakeCompany AWS ECS Deployment${NC}"
echo -e "${GREEN}========================================${NC}"

# Step 1: Navigate to backend directory
echo -e "\n${YELLOW}[1/6] Navigating to backend directory...${NC}"
cd "$(dirname "$0")/../backend"
pwd

# Step 2: Build Docker image for linux/amd64 (ECS Fargate requirement)
echo -e "\n${YELLOW}[2/6] Building Docker image for linux/amd64...${NC}"
docker buildx build --platform linux/amd64 -t ${IMAGE_NAME}:latest --load .
echo -e "${GREEN}✓ Docker image built successfully${NC}"

# Step 3: Login to AWS ECR
echo -e "\n${YELLOW}[3/6] Logging in to AWS ECR...${NC}"
aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com
echo -e "${GREEN}✓ ECR login successful${NC}"

# Step 4: Tag image for ECR
echo -e "\n${YELLOW}[4/6] Tagging image for ECR...${NC}"
docker tag ${IMAGE_NAME}:latest ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPOSITORY}:latest
echo -e "${GREEN}✓ Image tagged${NC}"

# Step 5: Push image to ECR
echo -e "\n${YELLOW}[5/6] Pushing image to ECR...${NC}"
docker push ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPOSITORY}:latest
echo -e "${GREEN}✓ Image pushed to ECR${NC}"

# Step 6: Force new ECS deployment
echo -e "\n${YELLOW}[6/6] Forcing new ECS deployment...${NC}"
aws ecs update-service \
    --cluster ${ECS_CLUSTER} \
    --service ${ECS_SERVICE} \
    --force-new-deployment \
    --region ${AWS_REGION}
echo -e "${GREEN}✓ ECS service update initiated${NC}"

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}Deployment Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "View logs at: https://console.aws.amazon.com/ecs/v2/clusters/${ECS_CLUSTER}/services/${ECS_SERVICE}/logs"
echo -e "Health check: http://telecorp-alb-35403735.us-east-1.elb.amazonaws.com/health"
