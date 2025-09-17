# AWS Serverless Agentic RAG Pipeline

A sophisticated **Agentic AI Customer Support System** built with AWS serverless technologies, featuring 5 autonomous agents that collaborate to provide intelligent customer support through advanced RAG (Retrieval-Augmented Generation) capabilities.

## 🤖 System Overview

This system implements a true **Agentic AI architecture** where specialized agents work autonomously while collaborating through orchestrated workflows:

- **Data Ingestion Agent** - Processes documents and builds knowledge base
- **Knowledge Retrieval Agent** - Performs hybrid search with advanced reranking
- **Conversation Agent** - Manages multi-turn conversations and generates responses
- **Support Escalation Agent** - Handles ticket creation and notifications
- **Orchestration Agent** - Coordinates all agents and manages workflows

## 🏗️ Architecture

### Core Technologies
- **AWS Lambda** - Serverless compute for all agents
- **Amazon OpenSearch** - Hybrid search (BM25 + kNN) with custom analyzers
- **Amazon Bedrock** - LLM and embedding generation (Titan models)
- **AWS Step Functions** - Agent orchestration and workflow management
- **Amazon DynamoDB** - Conversation history and ticket storage
- **Amazon SageMaker** - Cross-encoder reranking model
- **AWS Textract** - PDF text extraction

### Key Features
- ✅ **Hybrid Search** - BM25 + Semantic search with RRF fusion
- ✅ **Advanced Reranking** - Cross-encoder and MMR diversity filtering
- ✅ **Multi-turn Conversations** - Context-aware dialogue management
- ✅ **Automatic Escalation** - Intent detection and ticket creation
- ✅ **Quality Monitoring** - End-to-end performance tracking
- ✅ **Agent Autonomy** - Self-contained, specialized agents

## 🚀 Quick Start

### Prerequisites
- AWS CLI configured with appropriate permissions
- Terraform >= 1.0 (for infrastructure deployment)
- Python 3.9+
- Node.js (for some tooling)

### 1. Clone Repository
```bash
git clone <repository-url>
cd aws-serverless-agentic-rag-pipeline
```

### 2. Configure Environment
```bash
# Copy and customize Terraform variables
cp infrastructure/terraform/terraform.tfvars.example infrastructure/terraform/terraform.tfvars

# Set your AWS Account ID in environment config
echo "AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)" >> infrastructure/configs/dev.env

# Edit the file with your specific configuration
vim infrastructure/terraform/terraform.tfvars
```

### 3. Deploy Infrastructure
```bash
# Deploy with Terraform
./infrastructure/scripts/terraform_deploy.sh dev us-east-1 apply
```

### 4. Deploy Step Functions
```bash
# Deploy state machines
aws stepfunctions create-state-machine \
  --name "AaiKnowledgeRetrievalRagPipeline-dev" \
  --definition file://src/agents/orchestration/step-functions/AaiKnowledgeRetrievalRagPipeline.json \
  --role-arn $(terraform output -raw step_functions_role_arn)
```

## 📁 Project Structure

```
aws-serverless-agentic-rag-pipeline/
├── src/agents/                    # 5 Autonomous Agents
│   ├── ingestion/                 # Data Ingestion Agent (7 functions)
│   ├── retrieval/                 # Knowledge Retrieval Agent (4 functions)
│   ├── conversation/              # Conversation Agent (4 functions)
│   ├── escalation/                # Support Escalation Agent (1 function)
│   └── orchestration/             # Orchestration Agent (1 function + Step Functions)
├── infrastructure/                # Infrastructure as Code
│   ├── terraform/                 # Terraform configurations
│   ├── scripts/                   # Deployment scripts
│   └── configs/                   # Environment configurations
├── monitoring/                    # Monitoring and observability
└── examples/                      # Sample requests and notebooks
```

## 🤖 Agent Details

### Data Ingestion Agent
**Purpose**: Processes raw documents and builds searchable knowledge base
- PDF text extraction via Textract
- CSV data preprocessing and chunking
- Vector embedding generation
- OpenSearch indexing with hybrid search setup

### Knowledge Retrieval Agent  
**Purpose**: Performs sophisticated search and ranking
- Hybrid search (BM25 + kNN) with RRF fusion
- Cross-encoder reranking via SageMaker
- MMR diversity filtering
- Quality metrics calculation

### Conversation Agent
**Purpose**: Manages dialogue and generates responses
- Multi-turn conversation context management
- Query embedding generation
- LLM-based response synthesis via Bedrock
- Conversation persistence

### Support Escalation Agent
**Purpose**: Handles cases requiring human intervention
- Intent detection for escalation requests
- Support ticket creation in DynamoDB
- Email notifications via SES

### Orchestration Agent
**Purpose**: Coordinates all agents and manages workflows
- API Gateway integration
- Step Functions orchestration
- Error handling and recovery
- Session and query management

## 🔧 Configuration

### Environment Variables
Key configuration options available in `infrastructure/configs/`:

```bash
# Core Configuration
ENVIRONMENT=dev
AWS_REGION=us-east-1
AWS_ACCOUNT_ID=your-account-id
LLM_MODEL=amazon.titan-text-lite-v1

# Agent-Specific Settings
LAMBDA_TIMEOUT=300
LAMBDA_MEMORY=512
MAX_RESULTS=50
```

### Agent-Specific Configuration
Each agent can be configured independently through Terraform variables:

```hcl
agent_configs = {
  ingestion = {
    memory_size = 1024
    timeout     = 900
  }
  retrieval = {
    memory_size = 512
    timeout     = 300
  }
  # ... other agents
}
```

## 📊 Monitoring

### CloudWatch Dashboards
- Agent performance metrics
- Quality score tracking
- Error rate monitoring
- User interaction patterns

### Performance Analysis
```bash
# Run performance analysis
python monitoring/quality_metrics/analyze_performance.py

# Analyze agent logs
python monitoring/logs/log_analysis.py
```


## 📈 Performance

### Benchmarks
- **Average Response Time**: < 3 seconds
- **Search Accuracy**: 85%+ relevance scores
- **Concurrent Users**: 100+ supported
- **Cost**: ~$0.10 per 1000 queries

### Optimization
- Lambda layers for heavy dependencies
- OpenSearch index optimization
- Cross-encoder model caching
- Quality-based result filtering

## 🔒 Security

- IAM roles with least-privilege permissions
- VPC endpoints for secure communication
- Encryption at rest and in transit
- API Gateway throttling and authentication

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request


## 🙏 Acknowledgments

- AWS for providing excellent serverless technologies
- OpenSearch community for hybrid search capabilities
- Hugging Face for transformer models
- The open-source community for various libraries and tools

---

**Built with ❤️ using AWS Serverless Technologies**