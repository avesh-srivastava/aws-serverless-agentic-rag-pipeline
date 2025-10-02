# Defines variable declarations (what variables exist and their types)

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"
  
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod."
  }
}

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "ap-south-1"
}

variable "opensearch_domain" {
  description = "OpenSearch domain name"
  type        = string
  default     = "agentic-rag-kb"
}

variable "opensearch_index" {
  description = "OpenSearch index name"
  type        = string
  default     = "support-agent-knowledge"
}

variable "conversation_table_name" {
  description = "DynamoDB conversation table name"
  type        = string
  default     = "AaiConversationHistory-dev"
}

variable "support_tickets_table_name" {
  description = "DynamoDB support tickets table name"
  type        = string
  default     = "AaiSupportTickets-dev"
}

variable "hf_model_id" {
  description = "HuggingFace model ID for cross-encoder"
  type        = string
  default     = "cross-encoder/ms-marco-MiniLM-L-6-v2"
}

variable "hf_task" {
  description = "HuggingFace task type"
  type        = string
  default     = "text-classification"
}

variable "llm_model" {
  description = "Bedrock LLM model ID"
  type        = string
  default     = "amazon.titan-text-lite-v1"
}

variable "embed_model" {
  description = "Bedrock embedding model ID"
  type        = string
  default     = "amazon.titan-embed-text-v1"
}

variable "opensearch_instance_type" {
  description = "OpenSearch instance type"
  type        = string
  default     = "t3.small.search"
}

variable "opensearch_instance_count" {
  description = "Number of OpenSearch instances"
  type        = number
  default     = 1
}

variable "opensearch_volume_size" {
  description = "OpenSearch EBS volume size in GB"
  type        = number
  default     = 10
}

variable "lambda_timeout" {
  description = "Lambda function timeout in seconds"
  type        = number
  default     = 300
}

variable "lambda_memory_size" {
  description = "Lambda function memory size in MB"
  type        = number
  default     = 512
}

variable "ttl_days" {
  description = "DynamoDB TTL in days"
  type        = number
  default     = 7
}

variable "support_email" {
  description = "Support team email address"
  type        = string
  default     = "support@yourcompany.com"
}

variable "common_tags" {
  description = "Common tags to apply to all resources"
  type        = map(string)
  default = {
    Project     = "AgenticRAG"
    ManagedBy   = "Terraform"
    Application = "AI-Customer-Support"
  }
}

# Agent-specific variables
variable "agent_configs" {
  description = "Configuration for each agent"
  type = map(object({
    memory_size = number
    timeout     = number
    environment_vars = map(string)
  }))
  
  default = {
    ingestion = {
      memory_size = 1024
      timeout     = 900
      environment_vars = {
        CHUNK_BATCH_SIZE = "20"
        OUTPUT_PREFIX    = "processed/chunks/logs/"
        CHUNK_CHAR_SIZE  = "1200"
        CHUNK_OVERLAP    = "200"
      }
    }
    retrieval = {
      memory_size = 512
      timeout     = 300
      environment_vars = {}
    }
    conversation = {
      memory_size = 512
      timeout     = 300
      environment_vars = {
        PROMPT_MAX_CHARS = "3500"
        MAX_TURNS        = "5"
      }
    }
    escalation = {
      memory_size = 256
      timeout     = 60
      environment_vars = {}
    }
    orchestration = {
      memory_size = 256
      timeout     = 60
      environment_vars = {}
    }
  }
}