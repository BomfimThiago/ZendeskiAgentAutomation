# Deployment Scripts

This directory contains manual deployment scripts for MyAwesomeFakeCompany infrastructure.

## Prerequisites

### AWS Deployment
- AWS CLI configured with credentials
- Docker with buildx support
- Permissions to:
  - Push to ECR repository `myawesomefakecompany-api`
  - Update ECS service `telecorp-service` in cluster `telecorp-cluster`

### Vercel Deployment
- Vercel CLI installed (`npm i -g vercel`)
- Logged in to Vercel (`vercel login`)
- Linked to project `myawesomefakecompany`

## Usage

### Deploy Backend to AWS ECS

```bash
./scripts/deploy_aws.sh
```

**What it does:**
1. Builds Docker image for linux/amd64 (required for ECS Fargate)
2. Logs in to AWS ECR
3. Tags and pushes image to ECR
4. Forces new ECS deployment

**Estimated time:** 3-5 minutes

**Health check after deploy:**
```bash
curl http://telecorp-alb-35403735.us-east-1.elb.amazonaws.com/health
```

### Deploy Frontend to Vercel

```bash
./scripts/deploy_vercel.sh
```

**What it does:**
1. Navigates to frontend directory
2. Deploys to Vercel production

**Estimated time:** 1-2 minutes

## Configuration

If you need to change deployment targets, edit the following variables in the scripts:

**deploy_aws.sh:**
- `AWS_REGION` - Default: us-east-1
- `AWS_ACCOUNT_ID` - Default: 724772052980
- `ECR_REPOSITORY` - Default: myawesomefakecompany-api
- `ECS_CLUSTER` - Default: telecorp-cluster
- `ECS_SERVICE` - Default: telecorp-service

**deploy_vercel.sh:**
- No configuration needed (uses vercel.json in frontend/)

## Troubleshooting

### AWS Deployment Issues

**"exec format error"**
- The script already handles this by building for linux/amd64
- If you see this, verify Docker buildx is installed: `docker buildx version`

**"ECR login failed"**
- Check AWS credentials: `aws sts get-caller-identity`
- Verify region is correct

**ECS tasks failing health checks**
- Check CloudWatch logs: `/ecs/telecorp`
- Verify environment variables in ECS task definition

### Vercel Deployment Issues

**"Not logged in"**
```bash
vercel login
```

**"Project not linked"**
```bash
cd frontend && vercel link
```

## CI/CD

These scripts are designed for manual deployment. For automated deployments:
- Consider GitHub Actions for AWS (on push to main)
- Vercel automatically deploys on git push when connected to repository
