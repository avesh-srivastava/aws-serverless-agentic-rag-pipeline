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
  default     = "us-east-1"
}

variable "domain_name" {
  description = "OpenSearch domain name"
  type        = string
  default     = "agentic-rag-knowledge-base"
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
  default     = 20
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
        TEXTRACT_TIMEOUT = "300"
        CHUNK_SIZE       = "1000"
      }
    }
    retrieval = {
      memory_size = 512
      timeout     = 300
      environment_vars = {
        MAX_RESULTS      = "50"
        SEARCH_TIMEOUT   = "30"
      }
    }
    conversation = {
      memory_size = 512
      timeout     = 300
      environment_vars = {
        LLM_MODEL        = "amazon.titan-text-lite-v1"
        MAX_HISTORY      = "10"
      }
    }
    escalation = {
      memory_size = 256
      timeout     = 60
      environment_vars = {
        TICKET_PRIORITY  = "MEDIUM"
      }
    }
    orchestration = {
      memory_size = 256
      timeout     = 60
      environment_vars = {
        API_TIMEOUT      = "30"
      }
    }
  }
}