#!/bin/bash

# Deploy Lambda functions using Terraform outputs
# This script reads Terraform outputs and deploys all agent Lambda functions

set -e

ENVIRONMENT=${1:-dev}
REGION=${2:-ap-south-1}

echo "🤖 Deploying Lambda Functions - Environment: $ENVIRONMENT"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Load configuration files
TERRAFORM_OUTPUTS="infrastructure/configs/terraform-outputs-$ENVIRONMENT.json"
LAYER_CONFIG="infrastructure/configs/layer-config-$ENVIRONMENT.json"
STEP_FUNCTIONS_CONFIG="infrastructure/configs/step-functions-config-$ENVIRONMENT.json"

if [ ! -f "$TERRAFORM_OUTPUTS" ]; then
    echo -e "${RED}❌ Terraform outputs not found: $TERRAFORM_OUTPUTS${NC}"
    echo "Run terraform deployment first!"
    exit 1
fi

if [ ! -f "$LAYER_CONFIG" ]; then
    echo -e "${RED}❌ Layer config not found: $LAYER_CONFIG${NC}"
    echo "Run create_opensearch_layer.sh first!"
    exit 1
fi

if [ ! -f "$STEP_FUNCTIONS_CONFIG" ]; then
    echo -e "${RED}❌ Step Functions config not found: $STEP_FUNCTIONS_CONFIG${NC}"
    echo "Run deploy_step_functions.sh first!"
    exit 1
fi

# Extract values from configs
LAMBDA_ROLE_ARN=$(python -c "import json; data=json.load(open('$TERRAFORM_OUTPUTS')); print(data['lambda_role_arn']['value'])")
ENV_CONFIG=$(python -c "import json; data=json.load(open('$TERRAFORM_OUTPUTS')); print(json.dumps(data['environment_config']['value']))")
OPENSEARCH_LAYER_ARN=$(python -c "import json; data=json.load(open('$LAYER_CONFIG')); print(data['opensearch_layer_arn'])")
INGESTION_SF_ARN=$(python -c "import json; data=json.load(open('$STEP_FUNCTIONS_CONFIG')); print(data['ingestion_step_function_arn'])")
RETRIEVAL_SF_ARN=$(python -c "import json; data=json.load(open('$STEP_FUNCTIONS_CONFIG')); print(data['retrieval_step_function_arn'])")

echo -e "${BLUE}📋 Using Lambda Role: $LAMBDA_ROLE_ARN${NC}"
echo -e "${BLUE}🔌 Using OpenSearch Layer: $OPENSEARCH_LAYER_ARN${NC}"
echo -e "${BLUE}🎭 Using Step Functions:${NC}"
echo "  Ingestion: $INGESTION_SF_ARN"
echo "  Retrieval: $RETRIEVAL_SF_ARN"

# Function to deploy Lambda function
deploy_lambda() {
    local function_name=$1
    local source_path=$2
    local agent_name=$3
    local handler=${4:-lambda_function.lambda_handler}
    local needs_opensearch=${5:-false}
    local step_function_type=${6:-none}
    
    echo -e "${YELLOW}📦 Packaging $function_name ($agent_name agent)...${NC}"
    
    # Create deployment package
    cd "$source_path"
    
    # Install dependencies if requirements.txt exists (excluding AWS default packages)
    if [ -f "requirements.txt" ]; then
        echo "  📋 Installing dependencies (excluding AWS defaults)..."
        # Create filtered requirements without AWS default packages
        grep -v -E '^(boto3|botocore|opensearch-py|requests-aws4auth)' requirements.txt > filtered_requirements.txt 2>/dev/null || touch filtered_requirements.txt
        if [ -s filtered_requirements.txt ]; then
            pip install -r filtered_requirements.txt -t . --quiet
        fi
        rm -f filtered_requirements.txt
    fi
    
    # Create ZIP package using Python
    python -c "
import zipfile
import os
import sys

def create_zip(zip_path, source_dir):
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(source_dir):
            # Skip __pycache__ directories
            dirs[:] = [d for d in dirs if d != '__pycache__']
            for file in files:
                # Skip .pyc files
                if file.endswith('.pyc'):
                    continue
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, source_dir)
                zipf.write(file_path, arcname)

create_zip('../../../../../dist/$function_name.zip', '.')
"
    cd - > /dev/null
    
    # Get agent-specific configuration
    local memory_size=$(python -c "import json; data=json.loads('$ENV_CONFIG'); print(data.get('agent_configs', {}).get('$agent_name', {}).get('memory_size', 512))")
    local timeout=$(python -c "import json; data=json.loads('$ENV_CONFIG'); print(data.get('agent_configs', {}).get('$agent_name', {}).get('timeout', 300))")
    
    # Deploy Lambda function
    echo -e "${YELLOW}🚀 Deploying $function_name...${NC}"
    
    # Check if function exists, update or create accordingly
    if aws lambda get-function --function-name "$function_name" --region "$REGION" >/dev/null 2>&1; then
        echo "  🔄 Updating existing function..."
        aws lambda update-function-code \
            --function-name "$function_name" \
            --zip-file "fileb://dist/$function_name.zip" \
            --region "$REGION" > /dev/null
        
        # Wait for update to complete
        aws lambda wait function-updated --function-name "$function_name" --region "$REGION"
        
        # Add Step Function ARN to environment variables for updates
        local env_vars="ENVIRONMENT=$ENVIRONMENT,LAMBDA_FUNCTION_NAME=$function_name,AGENT_NAME=$agent_name"
        if [ "$step_function_type" = "ingestion" ]; then
            env_vars="$env_vars,STEP_FUNCTION_INGESTION_ARN=$INGESTION_SF_ARN"
        elif [ "$step_function_type" = "retrieval" ]; then
            env_vars="$env_vars,STEP_FUNCTION_RETRIEVAL_ARN=$RETRIEVAL_SF_ARN"
        fi
        
        # Update configuration
        aws lambda update-function-configuration \
            --function-name "$function_name" \
            --timeout "$timeout" \
            --memory-size "$memory_size" \
            --environment "Variables={$env_vars}" \
            --region "$REGION" > /dev/null
    else
        echo "  ✨ Creating new function..."
        # Add layers if needed
        local layers_param=""
        if [ "$needs_opensearch" = "true" ]; then
            layers_param="--layers $OPENSEARCH_LAYER_ARN"
        fi
        
        # Add Step Function ARN to environment variables
        local env_vars="ENVIRONMENT=$ENVIRONMENT,LAMBDA_FUNCTION_NAME=$function_name,AGENT_NAME=$agent_name"
        if [ "$step_function_type" = "ingestion" ]; then
            env_vars="$env_vars,STEP_FUNCTION_INGESTION_ARN=$INGESTION_SF_ARN"
        elif [ "$step_function_type" = "retrieval" ]; then
            env_vars="$env_vars,STEP_FUNCTION_RETRIEVAL_ARN=$RETRIEVAL_SF_ARN"
        fi
        
        aws lambda create-function \
            --function-name "$function_name" \
            --runtime python3.9 \
            --role "$LAMBDA_ROLE_ARN" \
            --handler "$handler" \
            --zip-file "fileb://dist/$function_name.zip" \
            --timeout "$timeout" \
            --memory-size "$memory_size" \
            --environment "Variables={$env_vars}" \
            $layers_param \
            --region "$REGION" > /dev/null
    fi
    
    echo -e "${GREEN}✅ $function_name deployed${NC}"
}

# Create dist directory
mkdir -p dist

echo "🤖 Deploying All Agents..."

# Deploy Ingestion Agent
echo -e "${YELLOW}📥 Deploying Ingestion Agent...${NC}"
deploy_lambda "aai_start_textract" "src/agents/ingestion/lambdas/aai_start_textract" "ingestion"
deploy_lambda "aai_check_textract_status" "src/agents/ingestion/lambdas/aai_check_textract_status" "ingestion"
deploy_lambda "aai_preprocess_csv" "src/agents/ingestion/lambdas/aai_preprocess_csv" "ingestion"
deploy_lambda "aai_chunk_text" "src/agents/ingestion/lambdas/aai_chunk_text" "ingestion"
deploy_lambda "aai_generate_embeddings" "src/agents/ingestion/lambdas/aai_generate_embeddings" "ingestion"
deploy_lambda "aai_store_opensearch" "src/agents/ingestion/lambdas/aai_store_opensearch" "ingestion" "lambda_function.lambda_handler" "true"
deploy_lambda "aai_create_opensearch_index" "src/agents/ingestion/lambdas/aai_create_opensearch_index" "ingestion" "lambda_function.lambda_handler" "true"

# Deploy Retrieval Agent
echo -e "${YELLOW}🔍 Deploying Retrieval Agent...${NC}"
deploy_lambda "aai_hybrid_search_fusion" "src/agents/retrieval/lambdas/aai_hybrid_search_fusion" "retrieval" "lambda_function.lambda_handler" "true"
deploy_lambda "aai_cross_encoder_rerank" "src/agents/retrieval/lambdas/aai_cross_encoder_rerank" "retrieval"
deploy_lambda "aai_mmr_diversity" "src/agents/retrieval/lambdas/aai_mmr_diversity" "retrieval"
deploy_lambda "aai_final_results" "src/agents/retrieval/lambdas/aai_final_results" "retrieval"

# Deploy Conversation Agent
echo -e "${YELLOW}💬 Deploying Conversation Agent...${NC}"
deploy_lambda "aai_read_history" "src/agents/conversation/lambdas/aai_read_history" "conversation"
deploy_lambda "aai_query_embedding" "src/agents/conversation/lambdas/aai_query_embedding" "conversation"
deploy_lambda "aai_synthesize_answer" "src/agents/conversation/lambdas/aai_synthesize_answer" "conversation"
deploy_lambda "aai_store_conversation" "src/agents/conversation/lambdas/aai_store_conversation" "conversation"

# Deploy Escalation Agent
echo -e "${YELLOW}🎫 Deploying Escalation Agent...${NC}"
deploy_lambda "aai_create_ticket" "src/agents/escalation/lambdas/aai_create_ticket" "escalation"

# Deploy Orchestration Agent
echo -e "${YELLOW}🎭 Deploying Orchestration Agent...${NC}"
deploy_lambda "aai_trigger_step_function_ingestion" "src/agents/orchestration/lambdas/aai_trigger_step_function_ingestion" "orchestration" "lambda_function.lambda_handler" "false" "ingestion"
deploy_lambda "aai_trigger_step_function_retrieval" "src/agents/orchestration/lambdas/aai_trigger_step_function_retrieval" "orchestration" "lambda_function.lambda_handler" "false" "retrieval"

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