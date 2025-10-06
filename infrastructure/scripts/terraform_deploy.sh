#!/bin/bash

# Agentic AI RAG Pipeline - Terraform Deployment Script
# Deploys infrastructure and Lambda functions using Terraform

set -e

ENVIRONMENT=${1:-dev}
REGION=${2:-ap-south-1}
ACTION=${3:-apply}

echo "🚀 Terraform Deployment - Environment: $ENVIRONMENT, Action: $ACTION"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Change to terraform directory
cd infrastructure/terraform

# Initialize Terraform
echo -e "${BLUE}🔧 Initializing Terraform...${NC}"
terraform init

# Validate configuration
echo -e "${BLUE}✅ Validating Terraform configuration...${NC}"
terraform validate

if [ "$ACTION" = "plan" ]; then
    echo -e "${YELLOW}📋 Creating Terraform plan...${NC}"
    terraform plan \
        -var="environment=$ENVIRONMENT" \
        -var="aws_region=$REGION" \
        -out="tfplan-$ENVIRONMENT"
    
    echo -e "${GREEN}✅ Terraform plan created: tfplan-$ENVIRONMENT${NC}"
    exit 0
fi

if [ "$ACTION" = "apply" ]; then
    echo -e "${YELLOW}🏗️  Applying Terraform configuration...${NC}"
    terraform apply \
        -var="environment=$ENVIRONMENT" \
        -var="aws_region=$REGION" \
        -auto-approve
    
    echo -e "${GREEN}✅ Infrastructure deployed successfully!${NC}"
    
    # Get outputs for Lambda deployment
    echo -e "${BLUE}📊 Getting Terraform outputs...${NC}"
    terraform output -json > "../configs/terraform-outputs-$ENVIRONMENT.json"
    
    cd ../..

    # Create OpenSearch layer first
    echo -e "${YELLOW}🔧 Creating OpenSearch Lambda layer...${NC}"
    ./infrastructure/scripts/create_opensearch_layer.sh "$ENVIRONMENT" "$REGION"
    
    # Deploy Step Functions
    echo -e "${YELLOW}🎭 Deploying Step Functions...${NC}"
    ./infrastructure/scripts/deploy_step_functions.sh "$ENVIRONMENT" "$REGION"
    
    # Lambda functions are already deployed by Terraform above
    
    # Configure S3 event notifications
    echo -e "${YELLOW}📬 Configuring S3 event notifications...${NC}"
    ./infrastructure/scripts/configure_s3_notifications.sh "$ENVIRONMENT" "$REGION"
    
elif [ "$ACTION" = "destroy" ]; then
    echo -e "${RED}⚠️  WARNING: This will destroy all infrastructure!${NC}"
    read -p "Are you sure? Type 'yes' to continue: " confirm
    
    if [ "$confirm" = "yes" ]; then
        echo -e "${RED}🗑️  Destroying infrastructure...${NC}"
        terraform destroy \
            -var="environment=$ENVIRONMENT" \
            -var="aws_region=$REGION" \
            -auto-approve
        
        echo -e "${GREEN}✅ Infrastructure destroyed${NC}"
    else
        echo -e "${YELLOW}❌ Destroy cancelled${NC}"
    fi
else
    echo -e "${RED}❌ Invalid action: $ACTION${NC}"
    echo "Usage: $0 <environment> <region> <plan|apply|destroy>"
    exit 1
fi

echo -e "${GREEN}🎉 Terraform deployment complete!${NC}"