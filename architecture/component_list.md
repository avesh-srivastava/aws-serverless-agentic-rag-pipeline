# Agentic AI Customer Support System - Component List

## **API Layer**
- **API Gateway**: REST API endpoint for customer interactions
- **Trigger Lambda** (`aai_trigger-step-function-to-generate-answer.py`): Entry point, session management, Step Function orchestration

## **Orchestration**
- **Step Functions** (`StateMachineRetrieval.json`): Complete RAG pipeline orchestration with error handling

## **Data Ingestion Pipeline**
- **S3 Raw Data**: Storage for CSV and PDF files
- **Textract Lambda** (`aai_lambda-start-textract`, `aai_lambda-check-textract-status`): PDF text extraction
- **Preprocess Lambda** (`aai_lambda_preprocess_chunk_csv.py`): CSV processing and chunking
- **Chunk Text Lambda** (`aai_lambda-chunk-text`): Text chunking for PDFs
- **Generate Embeddings** (`aai_lambda-generate-embeddings.py`): Vector embedding generation
- **Store Embeddings** (`aai_lambda-store-opensearch.py`): Index data in OpenSearch

## **Knowledge Base**
- **OpenSearch**: Hybrid search (BM25 + kNN) with custom analyzers
- **S3 Embeddings**: Storage for processed chunks and embeddings

## **Advanced Retrieval Pipeline**
- **Search & Fusion** (`lambda_1_search_fusion.py`): BM25 + kNN search with RRF fusion
- **Cross-Encoder** (`lambda_2_cross_encoder.py`): SageMaker-based reranking
- **MMR Diversity** (`lambda_3_mmr.py`): Maximal Marginal Relevance filtering
- **Final Results** (`lambda_4_final_results.py`): Quality metrics and result preparation
- **SageMaker Endpoint**: Cross-encoder model for reranking

## **Conversation Management**
- **Read History** (`aai_lambda-read-conversation-history`): Conversation context retrieval
- **Query Embedding** (`aai_lambda-get-query-embedding`): Query vectorization
- **Synthesize Answer** (`aai_lambda-synthesize-answer.py`): LLM-based response generation
- **Store Conversation** (`aai_store_conversation.py`): Conversation persistence
- **Create Ticket** (`aai_lambda_create_ticket.py`): Support ticket creation

## **AI Services**
- **Amazon Bedrock**: Titan models for embeddings and text generation
- **SageMaker**: Cross-encoder model hosting (`cross-encoder/ms-marco-MiniLM-L-6-v2`)

## **Storage**
- **DynamoDB - Conversations** (`AaiConversationHistory`): Session and conversation storage
- **DynamoDB - Tickets** (`SupportTickets`): Support ticket management
- **S3 - Monitoring**: Quality metrics and performance data

## **Monitoring & Notifications**
- **CloudWatch Metrics**: Performance monitoring across all components
- **CloudWatch Logs**: Detailed logging and error tracking
- **Amazon SES**: Email notifications for support tickets

## **Key Features**
- **Hybrid Search**: BM25 + Semantic search with RRF fusion
- **Advanced Reranking**: Cross-encoder and MMR diversity
- **Conversation Memory**: Multi-turn conversation support
- **Intent Detection**: Automatic ticket creation
- **Quality Monitoring**: End-to-end observability
- **Error Handling**: Graceful degradation and recovery
- **Scalability**: Serverless architecture with auto-scaling

## **Data Flow**
1. **Ingestion**: CSV/PDF → Processing → Embeddings → OpenSearch
2. **Query**: User → API Gateway → Step Function → Retrieval Pipeline
3. **Retrieval**: Hybrid Search → Reranking → MMR → Final Results
4. **Response**: LLM Synthesis → Conversation Storage → User Response
5. **Escalation**: Intent Detection → Ticket Creation → Email Notification