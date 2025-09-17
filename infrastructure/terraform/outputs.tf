output "opensearch_domain_endpoint" {
  description = "OpenSearch domain endpoint"
  value       = aws_opensearch_domain.agentic_rag.endpoint
}

output "opensearch_domain_arn" {
  description = "OpenSearch domain ARN"
  value       = aws_opensearch_domain.agentic_rag.arn
}

output "conversation_table_name" {
  description = "DynamoDB conversation history table name"
  value       = aws_dynamodb_table.conversation_history.name
}

output "conversation_table_arn" {
  description = "DynamoDB conversation history table ARN"
  value       = aws_dynamodb_table.conversation_history.arn
}

output "support_tickets_table_name" {
  description = "DynamoDB support tickets table name"
  value       = aws_dynamodb_table.support_tickets.name
}

output "support_tickets_table_arn" {
  description = "DynamoDB support tickets table ARN"
  value       = aws_dynamodb_table.support_tickets.arn
}

output "s3_bucket_name" {
  description = "S3 bucket for search results"
  value       = aws_s3_bucket.search_results.bucket
}

output "s3_bucket_arn" {
  description = "S3 bucket ARN"
  value       = aws_s3_bucket.search_results.arn
}

output "lambda_role_arn" {
  description = "Lambda execution role ARN"
  value       = aws_iam_role.lambda_role.arn
}

output "step_functions_role_arn" {
  description = "Step Functions execution role ARN"
  value       = aws_iam_role.step_functions_role.arn
}

output "sagemaker_role_arn" {
  description = "SageMaker execution role ARN"
  value       = aws_iam_role.sagemaker_role.arn
}

# Environment-specific outputs
output "environment_config" {
  description = "Environment configuration for Lambda functions"
  value = {
    ENVIRONMENT                = var.environment
    AWS_REGION                = var.aws_region
    DDB_CONVERSATION_TABLE    = aws_dynamodb_table.conversation_history.name
    DDB_TICKETS_TABLE         = aws_dynamodb_table.support_tickets.name
    S3_BUCKET                 = aws_s3_bucket.search_results.bucket
    OPENSEARCH_DOMAIN         = aws_opensearch_domain.agentic_rag.endpoint
    OPENSEARCH_INDEX          = "support-agent-knowledge"
    TTL_DAYS                  = var.ttl_days
    SUPPORT_EMAIL             = var.support_email
    LLM_MODEL                 = "amazon.titan-text-lite-v1"
    EMBEDDING_MODEL           = "amazon.titan-embed-text-v1"
  }
}

# Agent-specific role ARNs for deployment
output "agent_lambda_functions" {
  description = "Lambda function configuration for agents"
  value = {
    ingestion = {
      role_arn = aws_iam_role.lambda_role.arn
      functions = [
        "aai_start_textract",
        "aai_check_textract_status", 
        "aai_preprocess_csv",
        "aai_chunk_text",
        "aai_generate_embeddings",
        "aai_store_opensearch",
        "aai_create_opensearch_index"
      ]
    }
    retrieval = {
      role_arn = aws_iam_role.lambda_role.arn
      functions = [
        "aai_hybrid_search_fusion",
        "aai_cross_encoder_rerank",
        "aai_mmr_diversity", 
        "aai_final_results"
      ]
    }
    conversation = {
      role_arn = aws_iam_role.lambda_role.arn
      functions = [
        "aai_read_history",
        "aai_query_embedding",
        "aai_synthesize_answer",
        "aai_store_conversation"
      ]
    }
    escalation = {
      role_arn = aws_iam_role.lambda_role.arn
      functions = [
        "aai_create_ticket"
      ]
    }
    orchestration = {
      role_arn = aws_iam_role.lambda_role.arn
      functions = [
        "aai_trigger_step_function_retrieval"
      ]
    }
  }
}