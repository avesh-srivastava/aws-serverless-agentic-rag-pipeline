# Terraform Outputs
# These outputs are used by deployment scripts

output "lambda_role_arn" {
  description = "ARN of the Lambda execution role"
  value       = aws_iam_role.lambda_role.arn
}

output "step_functions_role_arn" {
  description = "ARN of the Step Functions execution role"
  value       = aws_iam_role.step_functions_role.arn
}

output "sagemaker_role_arn" {
  description = "ARN of the SageMaker execution role"
  value       = aws_iam_role.sagemaker_role.arn
}

output "sagemaker_endpoint_name" {
  description = "Name of the SageMaker cross-encoder endpoint"
  value       = aws_sagemaker_endpoint.cross_encoder.name
}

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

output "support_tickets_table_name" {
  description = "DynamoDB support tickets table name"
  value       = aws_dynamodb_table.support_tickets.name
}

output "search_results_bucket" {
  description = "S3 bucket for search results"
  value       = aws_s3_bucket.search_results.bucket
}

output "raw_data_bucket" {
  description = "S3 bucket for raw data"
  value       = aws_s3_bucket.raw_data.bucket
}

output "api_gateway_url" {
  description = "API Gateway endpoint URL"
  value       = "https://${aws_api_gateway_rest_api.agentic_rag_api.id}.execute-api.${data.aws_region.current.name}.amazonaws.com/${aws_api_gateway_stage.agentic_rag_stage.stage_name}"
}

output "api_gateway_getanswers_url" {
  description = "API Gateway getanswers endpoint URL"
  value       = "https://${aws_api_gateway_rest_api.agentic_rag_api.id}.execute-api.${data.aws_region.current.name}.amazonaws.com/${aws_api_gateway_stage.agentic_rag_stage.stage_name}/getanswers"
}

output "lambda_function_arns" {
  description = "ARNs of all Lambda functions"
  value = {
    for name, func in aws_lambda_function.agentic_rag_functions : name => func.arn
  }
}

output "lambda_function_names" {
  description = "Names of all Lambda functions"
  value = {
    for name, func in aws_lambda_function.agentic_rag_functions : name => func.function_name
  }
}

output "environment_config" {
  description = "Environment configuration for Lambda functions"
  value = {
    environment = var.environment
    aws_region  = var.aws_region
    
    # OpenSearch configuration
    opensearch_domain   = aws_opensearch_domain.agentic_rag.endpoint
    opensearch_index    = var.opensearch_index
    
    # DynamoDB configuration
    conversation_table  = aws_dynamodb_table.conversation_history.name
    support_tickets_table = aws_dynamodb_table.support_tickets.name
    
    # S3 configuration
    search_results_bucket = aws_s3_bucket.search_results.bucket
    raw_data_bucket      = aws_s3_bucket.raw_data.bucket
    
    # Model configuration
    hf_model_id = var.hf_model_id
    hf_task     = var.hf_task
    llm_model   = var.llm_model
    embed_model = var.embed_model
    
    # Application configuration
    ttl_days      = var.ttl_days
    support_email = var.support_email
    
    # Agent configurations
    agent_configs = var.agent_configs
  }
}