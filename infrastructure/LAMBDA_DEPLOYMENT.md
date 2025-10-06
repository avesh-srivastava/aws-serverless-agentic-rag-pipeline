# Lambda Function Deployment with Environment Variables

This document explains how to deploy Lambda functions with proper environment variables configured.

### Common Environment Variables (All Functions)
- `ENVIRONMENT` - Environment name (dev/staging/prod)
- `AWS_REGION` - AWS region
- `OPENSEARCH_DOMAIN` - OpenSearch domain endpoint
- `OPENSEARCH_INDEX` - OpenSearch index name
- `CONVERSATION_TABLE` - DynamoDB conversation table name
- `SUPPORT_TICKETS_TABLE` - DynamoDB support tickets table name
- `RAW_DATA_BUCKET` - S3 bucket for raw data
- `SEARCH_RESULTS_BUCKET` - S3 bucket for search results
- `LLM_MODEL` - Bedrock LLM model ID
- `EMBED_MODEL` - Bedrock embedding model ID
- `HF_MODEL_ID` - HuggingFace model ID
- `HF_TASK` - HuggingFace task type
- `SUPPORT_EMAIL` - Support team email
- `TTL_DAYS` - DynamoDB TTL in days

### Agent-Specific Environment Variables

#### Ingestion Agent
- `CHUNK_BATCH_SIZE` - Batch size for processing chunks
- `OUTPUT_PREFIX` - S3 output prefix for processed files
- `CHUNK_CHAR_SIZE` - Character size for text chunks
- `CHUNK_OVERLAP` - Overlap size between chunks

#### Conversation Agent
- `PROMPT_MAX_CHARS` - Maximum characters in prompts
- `MAX_TURNS` - Maximum conversation turns

## Deployment Methods

### Method 1: Full Infrastructure Deployment
```bash
# Deploy everything including Lambda functions
./infrastructure/scripts/terraform_deploy.sh dev ap-south-1 apply
```

### Method 2: Lambda Functions Only
```bash
# Deploy only Lambda functions (if infrastructure exists)
./infrastructure/scripts/deploy_lambdas_only.sh dev ap-south-1

# Or use Terraform targeting directly:
cd infrastructure/terraform
terraform apply -target=aws_lambda_function.agentic_rag_functions -auto-approve

# Deploy specific Lambda function
terraform apply -target=aws_lambda_function.agentic_rag_functions[\"aai_hybrid_search_fusion\"] -auto-approve
```

## Terraform Configuration

The Lambda functions are defined in `infrastructure/terraform/lambda_functions.tf` with:

1. **Automatic ZIP packaging** - Source code is automatically packaged
2. **Environment variable injection** - All required variables are set
3. **Agent-specific configuration** - Memory, timeout, and custom variables per agent
4. **CloudWatch log groups** - Automatic log group creation

## File Structure

```
infrastructure/
├── terraform/
│   ├── lambda_functions.tf      # Lambda function definitions
│   ├── lambda_packages/         # Generated ZIP files
│   └── ...
└── scripts/
    ├── deploy_lambdas_terraform.sh  # Terraform-based deployment
```

## Environment Variable Reference

For a complete list of environment variables and their purposes, see the `agent_configs` variable in `infrastructure/terraform/variables.tf`.