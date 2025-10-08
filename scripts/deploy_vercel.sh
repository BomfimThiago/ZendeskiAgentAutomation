#!/bin/bash

# Vercel Deployment Script for MyAwesomeFakeCompany Frontend
# This script deploys the React frontend to Vercel

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}MyAwesomeFakeCompany Vercel Deployment${NC}"
echo -e "${GREEN}========================================${NC}"

# Navigate to frontend directory
echo -e "\n${YELLOW}[1/2] Navigating to frontend directory...${NC}"
cd "$(dirname "$0")/../frontend"
pwd

# Deploy to Vercel (production)
echo -e "\n${YELLOW}[2/2] Deploying to Vercel (production)...${NC}"
vercel --prod

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}Deployment Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "Your frontend is now live on Vercel"
