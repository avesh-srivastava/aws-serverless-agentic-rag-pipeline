#!/bin/bash

# Deploy Step Functions State Machines
# This script deploys the Step Functions before Lambda functions

set -e

ENVIRONMENT=${1:-dev}
REGION=${2:-ap-south-1}

echo "🎭 Deploying Step Functions - Environment: $ENVIRONMENT"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Load Terraform outputs
TERRAFORM_OUTPUTS="infrastructure/configs/terraform-outputs-$ENVIRONMENT.json"

if [ ! -f "$TERRAFORM_OUTPUTS" ]; then
    echo -e "${RED}❌ Terraform outputs not found: $TERRAFORM_OUTPUTS${NC}"
    echo "Run terraform deployment first!"
    exit 1
fi

# Extract Step Functions role ARN
STEP_FUNCTIONS_ROLE_ARN=$(python -c "import json; data=json.load(open('$TERRAFORM_OUTPUTS')); print(data['step_functions_role_arn']['value'])")

echo -e "${BLUE}📋 Using Step Functions Role: $STEP_FUNCTIONS_ROLE_ARN${NC}"

# Function to deploy Step Function
deploy_step_function() {
    local state_machine_name=$1
    local definition_file=$2
    local type=$3
    local description=$4
    
    echo -e "${YELLOW}🚀 Deploying Step Function: $state_machine_name...${NC}"
    
    # Check if state machine exists
    if aws stepfunctions describe-state-machine --state-machine-arn "arn:aws:states:$REGION:$(aws sts get-caller-identity --query Account --output text):stateMachine:$state_machine_name" --region "$REGION" >/dev/null 2>&1; then
        echo "  🔄 Updating existing state machine..."
        aws stepfunctions update-state-machine \
            --state-machine-arn "arn:aws:states:$REGION:$(aws sts get-caller-identity --query Account --output text):stateMachine:$state_machine_name" \
            --definition "file://$definition_file" \
            --role-arn "$STEP_FUNCTIONS_ROLE_ARN" \
            --region "$REGION" > /dev/null
    else
        echo "  ✨ Creating new state machine..."
        aws stepfunctions create-state-machine \
            --name "$state_machine_name" \
            --definition "file://$definition_file" \
            --role-arn "$STEP_FUNCTIONS_ROLE_ARN" \
            --type "$type" \
            --region "$REGION" > /dev/null
    fi
    
    echo -e "${GREEN}✅ $state_machine_name deployed${NC}"
}

# Deploy Step Functions
echo -e "${YELLOW}🎭 Deploying Step Functions...${NC}"

# Deploy Knowledge Ingestion Pipeline
deploy_step_function \
    "AaiKnowledgeIngestionPipeline-$ENVIRONMENT" \
    "src/agents/orchestration/step-functions/AaiKnowledgeIngestionPipeline.json" \
    "STANDARD" \
    "Agentic AI Knowledge Ingestion Pipeline"

# Deploy Knowledge Retrieval RAG Pipeline  
deploy_step_function \
    "AaiKnowledgeRetrievalRagPipeline-$ENVIRONMENT" \
    "src/agents/orchestration/step-functions/AaiKnowledgeRetrievalRagPipeline.json" \
    "EXPRESS" \
    "Agentic AI Knowledge Retrieval RAG Pipeline"

# Save Step Function ARNs for Lambda deployment
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
INGESTION_SF_ARN="arn:aws:states:$REGION:$AWS_ACCOUNT_ID:stateMachine:AaiKnowledgeIngestionPipeline-$ENVIRONMENT"
RETRIEVAL_SF_ARN="arn:aws:states:$REGION:$AWS_ACCOUNT_ID:stateMachine:AaiKnowledgeRetrievalRagPipeline-$ENVIRONMENT"

# Save to config file
mkdir -p "infrastructure/configs"
cat > "infrastructure/configs/step-functions-config-$ENVIRONMENT.json" << EOF
{
  "ingestion_step_function_arn": "$INGESTION_SF_ARN",
  "retrieval_step_function_arn": "$RETRIEVAL_SF_ARN"
}
EOF

echo -e "${GREEN}🎉 Step Functions deployed successfully!${NC}"
echo -e "${BLUE}📋 Step Function ARNs:${NC}"
echo "Ingestion: $INGESTION_SF_ARN"
echo "Retrieval: $RETRIEVAL_SF_ARN"