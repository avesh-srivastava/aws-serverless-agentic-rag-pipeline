# Lambda Functions for Agentic RAG Pipeline

locals {
  # Common environment variables for all Lambda functions
  common_env_vars = {
    ENVIRONMENT           = var.environment
    OPENSEARCH_DOMAIN    = aws_opensearch_domain.agentic_rag.endpoint
    OPENSEARCH_INDEX     = var.opensearch_index
    CONVERSATION_TABLE   = aws_dynamodb_table.conversation_history.name
    SUPPORT_TICKETS_TABLE = aws_dynamodb_table.support_tickets.name
    RAW_DATA_BUCKET      = aws_s3_bucket.raw_data.bucket
    SEARCH_RESULTS_BUCKET = aws_s3_bucket.search_results.bucket
    LLM_MODEL            = var.llm_model
    EMBED_MODEL          = var.embed_model
    HF_MODEL_ID          = var.hf_model_id
    HF_TASK              = var.hf_task
    SAGEMAKER_ENDPOINT   = aws_sagemaker_endpoint.cross_encoder.name
    SUPPORT_EMAIL        = var.support_email
    TTL_DAYS             = tostring(var.ttl_days)
  }

  # Lambda function definitions
  lambda_functions = {
    # Ingestion Agent Functions
    "aai_start_textract" = {
      agent = "ingestion"
      source_dir = "${path.root}/../../src/agents/ingestion/lambdas/aai_start_textract"
    }
    "aai_check_textract_status" = {
      agent = "ingestion"
      source_dir = "${path.root}/../../src/agents/ingestion/lambdas/aai_check_textract_status"
    }
    "aai_preprocess_csv" = {
      agent = "ingestion"
      source_dir = "${path.root}/../../src/agents/ingestion/lambdas/aai_preprocess_csv"
    }
    "aai_chunk_text" = {
      agent = "ingestion"
      source_dir = "${path.root}/../../src/agents/ingestion/lambdas/aai_chunk_text"
    }
    "aai_generate_embeddings" = {
      agent = "ingestion"
      source_dir = "${path.root}/../../src/agents/ingestion/lambdas/aai_generate_embeddings"
    }
    "aai_create_opensearch_index" = {
      agent = "ingestion"
      source_dir = "${path.root}/../../src/agents/ingestion/lambdas/aai_create_opensearch_index"
    }
    "aai_store_opensearch" = {
      agent = "ingestion"
      source_dir = "${path.root}/../../src/agents/ingestion/lambdas/aai_store_opensearch"
    }
    
    # Retrieval Agent Functions
    "aai_hybrid_search_fusion" = {
      agent = "retrieval"
      source_dir = "${path.root}/../../src/agents/retrieval/lambdas/aai_hybrid_search_fusion"
    }
    "aai_cross_encoder_rerank" = {
      agent = "retrieval"
      source_dir = "${path.root}/../../src/agents/retrieval/lambdas/aai_cross_encoder_rerank"
    }
    "aai_mmr_diversity" = {
      agent = "retrieval"
      source_dir = "${path.root}/../../src/agents/retrieval/lambdas/aai_mmr_diversity"
    }
    "aai_final_results" = {
      agent = "retrieval"
      source_dir = "${path.root}/../../src/agents/retrieval/lambdas/aai_final_results"
    }
    
    # Conversation Agent Functions
    "aai_query_embedding" = {
      agent = "conversation"
      source_dir = "${path.root}/../../src/agents/conversation/lambdas/aai_query_embedding"
    }
    "aai_read_history" = {
      agent = "conversation"
      source_dir = "${path.root}/../../src/agents/conversation/lambdas/aai_read_history"
    }
    "aai_synthesize_answer" = {
      agent = "conversation"
      source_dir = "${path.root}/../../src/agents/conversation/lambdas/aai_synthesize_answer"
    }
    "aai_store_conversation" = {
      agent = "conversation"
      source_dir = "${path.root}/../../src/agents/conversation/lambdas/aai_store_conversation"
    }
    
    # Escalation Agent Functions
    "aai_create_ticket" = {
      agent = "escalation"
      source_dir = "${path.root}/../../src/agents/escalation/lambdas/aai_create_ticket"
    }
    
    # Orchestration Agent Functions
    "aai_trigger_step_function_ingestion" = {
      agent = "orchestration"
      source_dir = "${path.root}/../../src/agents/orchestration/lambdas/aai_trigger_step_function_ingestion"
    }
    "aai_trigger_step_function_retrieval" = {
      agent = "orchestration"
      source_dir = "${path.root}/../../src/agents/orchestration/lambdas/aai_trigger_step_function_retrieval"
    }
  }
}

# Create ZIP files for Lambda functions
data "archive_file" "lambda_zip" {
  for_each = local.lambda_functions
  
  type        = "zip"
  source_dir  = each.value.source_dir
  output_path = "${path.module}/lambda_packages/${each.key}.zip"
  
  excludes = [
    "__pycache__",
    "*.pyc",
    ".git"
  ]
}

# Lambda Functions
resource "aws_lambda_function" "agentic_rag_functions" {
  for_each = local.lambda_functions

  function_name = each.key
  role         = aws_iam_role.lambda_role.arn
  handler      = "lambda_function.lambda_handler"
  runtime      = "python3.9"
  timeout      = var.agent_configs[each.value.agent].timeout
  memory_size  = var.agent_configs[each.value.agent].memory_size

  filename         = data.archive_file.lambda_zip[each.key].output_path
  source_code_hash = data.archive_file.lambda_zip[each.key].output_base64sha256

  environment {
    variables = merge(
      local.common_env_vars,
      var.agent_configs[each.value.agent].environment_vars,
      {
        AGENT_NAME           = each.value.agent
        LAMBDA_FUNCTION_NAME = each.key
      }
    )
  }

  tags = var.common_tags

  depends_on = [
    aws_iam_role_policy_attachment.lambda_basic,
    aws_iam_role_policy.lambda_permissions
  ]
}

