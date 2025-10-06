# AWS Serverless Agentic RAG Pipeline - Deployment Guide

Complete deployment guide for the Agentic AI Customer Support System with environment-specific configurations.

## 📋 Table of Contents

1. [Quick Start](#quick-start)
2. [Environment Configurations](#environment-configurations)
3. [Deployment Methods](#deployment-methods)
4. [Lambda Functions](#lambda-functions)
5. [SageMaker Endpoint](#sagemaker-endpoint)
6. [Environment Variables](#environment-variables)
7. [Monitoring & Troubleshooting](#monitoring--troubleshooting)

## 🚀 Quick Start

### Prerequisites
- AWS CLI configured with appropriate permissions
- Terraform >= 1.0
- Python 3.9+

### 1. Clone and Configure
```bash
git clone <repository-url>
cd aws-serverless-agentic-rag-pipeline

# Set your AWS Account ID
echo "AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)" >> infrastructure/configs/dev.env
```

### 2. Choose Environment Configuration
```bash
# For Development
cp infrastructure/terraform/terraform.tfvars.dev infrastructure/terraform/terraform.tfvars

# For Production
cp infrastructure/terraform/terraform.tfvars.prod infrastructure/terraform/terraform.tfvars
```

### 3. Deploy Infrastructure
```bash
./infrastructure/scripts/terraform_deploy.sh dev ap-south-1 apply
```

## 🏗️ Environment Configurations

### Development Environment (`terraform.tfvars.dev`)
- **Purpose**: Minimal configuration for development and testing
- **Cost**: ~$200-400/month
- **Performance**: Basic performance suitable for development

**Key Settings:**
- OpenSearch: t3.small.search, 1 node, 20GB
- Lambda: 512MB-1024MB memory
- DynamoDB: Pay-per-request
- No reserved concurrency

### Production Environment (`terraform.tfvars.prod`)
- **Purpose**: Production-ready configuration with high availability
- **Cost**: ~$800-1,200/month
- **Performance**: Optimized for production workloads

**Key Settings:**
- OpenSearch: r6g.large.search, 3 nodes + dedicated masters, 100GB each
- Lambda: 1024MB-3008MB memory with reserved/provisioned concurrency
- DynamoDB: Provisioned capacity with auto-scaling
- Enhanced monitoring and error handling

### Configuration Comparison

| Component | Development | Production |
|-----------|-------------|------------|
| **OpenSearch** | t3.small.search, 1 node, 20GB | r6g.large.search, 3 nodes, 100GB each |
| **Lambda Memory** | 512MB-1024MB | 1024MB-3008MB |
| **Lambda Concurrency** | Default | Reserved + Provisioned |
| **DynamoDB TTL** | 7 days | 30 days |
| **Monitoring** | Basic | Enhanced with detailed metrics |
| **High Availability** | Single AZ | Multi-AZ with dedicated masters |
| **Expected Performance** | <5,000 docs/day, 100 users | <15,000 docs/day, 500+ users |

## 🛠️ Deployment Methods

### Method 1: Full Infrastructure Deployment (Recommended)
```bash
# Deploy everything including Lambda functions
./infrastructure/scripts/terraform_deploy.sh <environment> <region> apply

# Examples:
./infrastructure/scripts/terraform_deploy.sh dev ap-south-1 apply
./infrastructure/scripts/terraform_deploy.sh prod ap-south-1 apply
```

### Method 2: Lambda Functions Only
```bash
# Deploy only Lambda functions (if infrastructure exists)
./infrastructure/scripts/deploy_lambdas_only.sh dev ap-south-1

# Or use Terraform targeting directly:
cd infrastructure/terraform
terraform apply -target=aws_lambda_function.agentic_rag_functions -auto-approve
```

### Method 3: Specific Components
```bash
# Deploy specific Lambda function
terraform apply -target=aws_lambda_function.agentic_rag_functions[\"aai_hybrid_search_fusion\"] -auto-approve

# Deploy OpenSearch only
terraform apply -target=aws_opensearch_domain.agentic_rag -auto-approve

# Deploy DynamoDB tables only
terraform apply -target=aws_dynamodb_table.conversation_history -target=aws_dynamodb_table.support_tickets -auto-approve
```

## 🤖 Lambda Functions

### Function Architecture
The system includes 17 Lambda functions across 5 agents:

**Data Ingestion Agent (7 functions):**
- `aai_start_textract` - Initiates PDF text extraction
- `aai_check_textract_status` - Monitors extraction progress
- `aai_preprocess_csv` - Processes CSV files
- `aai_chunk_text` - Splits documents into chunks
- `aai_generate_embeddings` - Creates vector embeddings
- `aai_create_opensearch_index` - Sets up search index
- `aai_store_opensearch` - Stores documents in search index

**Knowledge Retrieval Agent (4 functions):**
- `aai_hybrid_search_fusion` - Performs BM25 + kNN search
- `aai_cross_encoder_rerank` - Advanced result reranking
- `aai_mmr_diversity` - Ensures result diversity
- `aai_final_results` - Compiles final search results

**Conversation Agent (4 functions):**
- `aai_query_embedding` - Generates query embeddings
- `aai_read_history` - Retrieves conversation history
- `aai_synthesize_answer` - Generates responses via Bedrock
- `aai_store_conversation` - Persists conversation data

**Support Escalation Agent (1 function):**
- `aai_create_ticket` - Creates support tickets

**Orchestration Agent (2 functions):**
- `aai_trigger_step_function_ingestion` - Triggers ingestion workflow
- `aai_trigger_step_function_retrieval` - Triggers retrieval workflow

### Lambda Configuration Features
- **Automatic ZIP packaging** - Source code automatically packaged
- **Environment variable injection** - All required variables set
- **Agent-specific configuration** - Memory, timeout, and custom variables per agent
- **CloudWatch log groups** - Automatic log group creation
- **Concurrency controls** - Reserved and provisioned concurrency in production

## 🧠 SageMaker Endpoint

### Deploy Cross-Encoder Model
```bash
# Deploy SageMaker serverless endpoint for reranking
python infrastructure/scripts/deploy_sagemaker_endpoint.py
```

**Configuration:**
- **Model**: cross-encoder/ms-marco-MiniLM-L-6-v2
- **Memory**: 3GB (dev) / 6GB (prod)
- **Concurrency**: 5 (dev) / 50 (prod)
- **Type**: Serverless (pay-per-use)

## 🔧 Environment Variables

### Common Variables (All Functions)
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
- `SAGEMAKER_ENDPOINT` - SageMaker endpoint name
- `SUPPORT_EMAIL` - Support team email
- `TTL_DAYS` - DynamoDB TTL in days

### Agent-Specific Variables

#### Ingestion Agent
- `CHUNK_BATCH_SIZE` - Batch size for processing chunks
- `OUTPUT_PREFIX` - S3 output prefix for processed files
- `CHUNK_CHAR_SIZE` - Character size for text chunks
- `CHUNK_OVERLAP` - Overlap size between chunks

#### Retrieval Agent (Production)
- `SEARCH_TIMEOUT_MS` - Search operation timeout
- `MAX_SEARCH_RESULTS` - Maximum search results
- `RERANK_BATCH_SIZE` - Reranking batch size
- `CACHE_TTL_SECONDS` - Result cache TTL
- `PERFORMANCE_MODE` - Performance optimization mode

#### Conversation Agent
- `PROMPT_MAX_CHARS` - Maximum characters in prompts
- `MAX_TURNS` - Maximum conversation turns
- `RESPONSE_TIMEOUT_MS` - Response generation timeout (prod)
- `CONTEXT_WINDOW_SIZE` - Context window size (prod)
- `QUALITY_THRESHOLD` - Response quality threshold (prod)

## 📊 Monitoring & Troubleshooting

### CloudWatch Logs
```bash
# View Lambda function logs
aws logs describe-log-groups --log-group-name-prefix "/aws/lambda/aai_"

# View Step Functions logs
aws logs describe-log-groups --log-group-name-prefix "/aws/stepfunctions/"
```

### Step Functions Monitoring
```bash
# List executions
aws stepfunctions list-executions --state-machine-arn "arn:aws:states:ap-south-1:ACCOUNT:stateMachine:AaiKnowledgeRetrievalRagPipeline-dev"

# Test retrieval pipeline
aws stepfunctions start-sync-execution \
  --state-machine-arn "arn:aws:states:ap-south-1:ACCOUNT:stateMachine:AaiKnowledgeRetrievalRagPipeline-dev" \
  --input '{"user_query": "What are your business hours?", "session_id": "test-session", "query_id": "test-query", "max_results": 5, "use_reranker": true, "use_mmr": true, "mmr_lambda": 0.7, "product_filter": null}'
```

### Common Issues

**Lambda Environment Variables Missing:**
```bash
# Update Lambda environment variables
python infrastructure/scripts/update_lambda_env_vars.py
```

**OpenSearch Index Issues:**
```bash
# Recreate OpenSearch index
aws lambda invoke --function-name aai_create_opensearch_index response.json
```

**SageMaker Endpoint Not Found:**
```bash
# Redeploy SageMaker endpoint
python infrastructure/scripts/deploy_sagemaker_endpoint.py
```

## 🔄 Migration Path (Dev to Prod)

### 1. Backup Development Data
```bash
# Export DynamoDB data
aws dynamodb scan --table-name AaiConversationHistory-dev --output json > conversation-backup.json

# Export OpenSearch indices (use snapshot functionality)
```

### 2. Deploy Production Environment
```bash
cp infrastructure/terraform/terraform.tfvars.prod infrastructure/terraform/terraform.tfvars
./infrastructure/scripts/terraform_deploy.sh prod ap-south-1 apply
```

### 3. Update Application Endpoints
- Update API Gateway custom domain
- Update application configuration

## 📁 File Structure

```
infrastructure/
├── terraform/
│   ├── lambda_functions.tf          # Lambda function definitions
│   ├── main.tf                      # Core infrastructure
│   ├── variables.tf                 # Variable declarations
│   ├── terraform.tfvars.dev         # Development configuration
│   ├── terraform.tfvars.prod        # Production configuration
│   └── lambda_packages/             # Generated ZIP files
├── scripts/
│   ├── terraform_deploy.sh          # Main deployment script
│   ├── deploy_lambdas_only.sh       # Lambda-only deployment
│   ├── deploy_sagemaker_endpoint.py # SageMaker deployment
│   └── update_lambda_env_vars.py    # Environment variable updates
└── configs/
    └── terraform-outputs-dev.json   # Terraform outputs
```

## 🎯 Next Steps

1. **Deploy Infrastructure**: Choose your environment and deploy
2. **Ingest Sample Data**: Upload documents to test the system
3. **Test End-to-End**: Verify the complete pipeline works
4. **Monitor Performance**: Set up CloudWatch dashboards
5. **Scale as Needed**: Adjust configurations based on usage

---

For detailed implementation guides, see:
- [Part 2: Data Ingestion Workflow Pipeline](https://medium.com/@avesh-srivastava/from-information-silos-to-intelligent-support-building-a-serverless-agentic-rag-pipeline-on-aws-81922f6a6cc3)
- [Part 3: Data Retrieval Workflow Pipeline](https://avesh-srivastava.medium.com/from-information-silos-to-intelligent-support-building-a-serverless-agentic-rag-pipeline-on-aws-099385907b29)
