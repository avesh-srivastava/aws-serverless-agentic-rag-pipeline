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
- Terraform >= 1.0
- Python 3.9+

### 1. Clone Repository
```bash
git clone <repository-url>
cd aws-serverless-agentic-rag-pipeline
```

### 2. Choose Environment Configuration
```bash
# For Development (minimal cost)
cp infrastructure/terraform/terraform.tfvars.dev infrastructure/terraform/terraform.tfvars

# For Production (high availability)
cp infrastructure/terraform/terraform.tfvars.prod infrastructure/terraform/terraform.tfvars
```

### 3. Deploy Infrastructure
```bash
# Deploy complete system
./infrastructure/scripts/terraform_deploy.sh dev ap-south-1 apply
```

📖 **For detailed deployment instructions, see [DEPLOYMENT.md](infrastructure/DEPLOYMENT.md)**

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
├── notebooks/                     # Jupyter notebooks for data analysis
├── sample-data/                   # Sample data for testing
│   ├── business-documents/        # Business and process documents
│   ├── products/                  # Product specifications
│   ├── faqs/                      # Customer support FAQs
│   └── support-tickets/           # Kaggle support ticket dataset
└── examples/                      # Sample requests and notebooks
```

## 🤖 Agent Details

### Data Ingestion Agent
**Purpose**: Processes raw documents and builds searchable knowledge base
- PDF text extraction via Textract
- CSV data preprocessing and chunking
- Vector embedding generation
- OpenSearch indexing with hybrid search setup

**📝 Production Note**: For concurrent file uploads >100/min, add SQS buffer between S3 and Lambda to prevent throttling and enable retry mechanisms.

### Knowledge Retrieval Agent  
**Purpose**: Performs sophisticated search and ranking
- Hybrid search (BM25 + kNN) with RRF fusion
- Cross-encoder reranking via SageMaker
- MMR diversity filtering
- Quality metrics calculation

**📝 Production Note**: For complex queries >5 minutes, switch to Standard Step Functions instead of Express for extended processing time and detailed execution history.

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

### Environment Options
- **Development**: Minimal cost configuration (~$200-400/month)
- **Production**: High availability configuration (~$800-1,200/month)

### Key Components
- **17 Lambda Functions** across 5 specialized agents
- **OpenSearch** with hybrid search capabilities
- **SageMaker** serverless endpoint for reranking
- **Step Functions** for workflow orchestration
- **DynamoDB** for conversation and ticket storage

📖 **For complete configuration details, see [DEPLOYMENT.md](infrastructure/DEPLOYMENT.md)**

## 📈 Performance & Monitoring

### Development Environment
- **Response Time**: < 3 seconds
- **Concurrent Users**: 100+
- **Daily Volume**: < 5,000 documents
- **Cost**: ~$0.10 per 1000 queries

### Production Environment
- **Response Time**: < 1.5 seconds
- **Concurrent Users**: 500+
- **Daily Volume**: < 15,000 documents
- **Search Accuracy**: 85%+ relevance scores

### Built-in Monitoring
- CloudWatch dashboards and alarms
- Step Functions execution tracking
- Lambda performance metrics
- Quality score monitoring

## 🔒 Security

- IAM roles with least-privilege permissions
- VPC endpoints for secure communication
- Encryption at rest and in transit
- API Gateway throttling and authentication

## 🚀 Production Scaling

### High-Volume Enhancements

**For Concurrent File Processing (>100 files/min):**
```
S3 → SQS → Lambda (with DLQ for error handling)
```

**For Complex Queries (>5 minutes):**
```
Standard Step Functions (instead of Express)
```

**When to Scale:**
- Add SQS buffer for high-volume document ingestion
- Switch to Standard Step Functions for complex processing
- Consider batch processing for enterprise document sets

## 📚 Documentation

- **[Deployment Guide](infrastructure/DEPLOYMENT.md)** - Complete deployment instructions
- **[Project Overview](https://avesh-srivastava.medium.com/from-information-silos-to-intelligent-support-building-a-serverless-agentic-rag-pipeline-on-aws-594df66d8b48)** - Business case and architecture
- **[Data Ingestion Pipeline](https://avesh-srivastava.medium.com/from-information-silos-to-intelligent-support-building-a-serverless-agentic-rag-pipeline-on-aws-81922f6a6cc3)** - Document processing workflow
- **[Data Retrieval Pipeline](https://avesh-srivastava.medium.com/from-information-silos-to-intelligent-support-building-a-serverless-agentic-rag-pipeline-on-aws-099385907b29)** - Search and response generation

## 🙏 Acknowledgments

- AWS for providing excellent serverless technologies
- OpenSearch community for hybrid search capabilities
- Hugging Face for transformer models
- The open-source community for various libraries and tools

---

**Built with ❤️ using AWS Serverless Technologies**