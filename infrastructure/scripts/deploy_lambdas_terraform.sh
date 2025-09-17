#!/bin/bash

# Deploy Lambda functions using Terraform outputs
# This script reads Terraform outputs and deploys all agent Lambda functions

set -e

ENVIRONMENT=${1:-dev}
REGION=${2:-us-east-1}

echo "🤖 Deploying Lambda Functions - Environment: $ENVIRONMENT"

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

# Extract values from Terraform outputs
LAMBDA_ROLE_ARN=$(jq -r '.lambda_role_arn.value' "$TERRAFORM_OUTPUTS")
ENV_CONFIG=$(jq -r '.environment_config.value' "$TERRAFORM_OUTPUTS")

echo -e "${BLUE}📋 Using Lambda Role: $LAMBDA_ROLE_ARN${NC}"

# Function to deploy Lambda function
deploy_lambda() {
    local function_name=$1
    local source_path=$2
    local agent_name=$3
    local handler=${4:-lambda_function.lambda_handler}
    
    echo -e "${YELLOW}📦 Packaging $function_name ($agent_name agent)...${NC}"
    
    # Create deployment package
    cd "$source_path"
    
    # Install dependencies if requirements.txt exists
    if [ -f "requirements.txt" ]; then
        echo "  📋 Installing dependencies..."
        pip install -r requirements.txt -t . --quiet
    fi
    
    # Create ZIP package
    zip -r "../../../../../dist/$function_name.zip" . -x "*.pyc" "__pycache__/*" > /dev/null
    cd - > /dev/null
    
    # Get agent-specific configuration
    local memory_size=$(echo "$ENV_CONFIG" | jq -r --arg agent "$agent_name" '.agent_configs[$agent].memory_size // 512')
    local timeout=$(echo "$ENV_CONFIG" | jq -r --arg agent "$agent_name" '.agent_configs[$agent].timeout // 300')
    
    # Deploy Lambda function
    echo -e "${YELLOW}🚀 Deploying $function_name...${NC}"
    
    # Create environment variables JSON
    local env_vars=$(echo "$ENV_CONFIG" | jq -c '. + {
        "LAMBDA_FUNCTION_NAME": "'$function_name'",
        "AGENT_NAME": "'$agent_name'"
    }')
    
    # Try to update existing function, create if it doesn't exist
    aws lambda update-function-code \
        --function-name "$function_name" \
        --zip-file "fileb://dist/$function_name.zip" \
        --region "$REGION" 2>/dev/null || \
    aws lambda create-function \
        --function-name "$function_name" \
        --runtime python3.9 \
        --role "$LAMBDA_ROLE_ARN" \
        --handler "$handler" \
        --zip-file "fileb://dist/$function_name.zip" \
        --timeout "$timeout" \
        --memory-size "$memory_size" \
        --environment "Variables=$env_vars" \
        --region "$REGION" > /dev/null
    
    # Update function configuration
    aws lambda update-function-configuration \
        --function-name "$function_name" \
        --timeout "$timeout" \
        --memory-size "$memory_size" \
        --environment "Variables=$env_vars" \
        --region "$REGION" > /dev/null
    
    echo -e "${GREEN}✅ $function_name deployed${NC}"
}

# Create dist directory
mkdir -p dist

echo "🤖 Deploying All Agents..."

# Deploy Ingestion Agent
echo -e "${YELLOW}📥 Deploying Ingestion Agent...${NC}"
deploy_lambda "aai_start_textract" "src/agents/ingestion/lambdas/textract" "ingestion"
deploy_lambda "aai_check_textract_status" "src/agents/ingestion/lambdas/textract" "ingestion"
deploy_lambda "aai_preprocess_csv" "src/agents/ingestion/lambdas/preprocessing" "ingestion"
deploy_lambda "aai_chunk_text" "src/agents/ingestion/lambdas/preprocessing" "ingestion"
deploy_lambda "aai_generate_embeddings" "src/agents/ingestion/lambdas/embeddings" "ingestion"
deploy_lambda "aai_store_opensearch" "src/agents/ingestion/lambdas/embeddings" "ingestion"
deploy_lambda "aai_create_opensearch_index" "src/agents/ingestion/lambdas/setup" "ingestion"

# Deploy Retrieval Agent
echo -e "${YELLOW}🔍 Deploying Retrieval Agent...${NC}"
deploy_lambda "aai_hybrid_search_fusion" "src/agents/retrieval/lambdas/search" "retrieval"
deploy_lambda "aai_cross_encoder_rerank" "src/agents/retrieval/lambdas/reranking" "retrieval"
deploy_lambda "aai_mmr_diversity" "src/agents/retrieval/lambdas/reranking" "retrieval"
deploy_lambda "aai_final_results" "src/agents/retrieval/lambdas/results" "retrieval"

# Deploy Conversation Agent
echo -e "${YELLOW}💬 Deploying Conversation Agent...${NC}"
deploy_lambda "aai_read_history" "src/agents/conversation/lambdas/history" "conversation"
deploy_lambda "aai_query_embedding" "src/agents/conversation/lambdas/embedding" "conversation"
deploy_lambda "aai_synthesize_answer" "src/agents/conversation/lambdas/synthesis" "conversation"
deploy_lambda "aai_store_conversation" "src/agents/conversation/lambdas/storage" "conversation"

# Deploy Escalation Agent
echo -e "${YELLOW}🎫 Deploying Escalation Agent...${NC}"
deploy_lambda "aai_create_ticket" "src/agents/escalation/lambdas/ticketing" "escalation"

# Deploy Orchestration Agent
echo -e "${YELLOW}🎭 Deploying Orchestration Agent...${NC}"
deploy_lambda "aai_trigger_step_function_retrieval" "src/agents/orchestration/lambdas/trigger" "orchestration"

echo -e "${GREEN}🎉 All Lambda functions deployed successfully!${NC}"
echo -e "${YELLOW}📋 Next steps:${NC}"
echo "1. Deploy Step Functions state machines"
echo "2. Configure API Gateway"
echo "3. Set up monitoring dashboards"

# Display deployment summary
echo -e "\n${BLUE}📊 Deployment Summary:${NC}"
echo "Environment: $ENVIRONMENT"
echo "Region: $REGION"
echo "Lambda Role: $LAMBDA_ROLE_ARN"
echo "Functions Deployed: 17"
echo "Agents: 5 (Ingestion, Retrieval, Conversation, Escalation, Orchestration)"