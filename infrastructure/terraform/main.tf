terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# Data sources
data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

# OpenSearch Domain
resource "aws_opensearch_domain" "agentic_rag" {
  domain_name    = "${var.opensearch_domain}-${var.environment}"
  engine_version = "OpenSearch_3.1"

  cluster_config {
    instance_type          = var.opensearch_instance_type
    instance_count         = var.opensearch_instance_count
    zone_awareness_enabled = false
  }

  ebs_options {
    ebs_enabled = true
    volume_type = "gp3"
    volume_size = var.opensearch_volume_size
  }

  domain_endpoint_options {
    enforce_https       = true
    tls_security_policy = "Policy-Min-TLS-1-2-2019-07"
  }

  node_to_node_encryption {
    enabled = true
  }

  encrypt_at_rest {
    enabled = true
  }

  advanced_security_options {
    enabled                        = true
    anonymous_auth_enabled         = false
    internal_user_database_enabled = false
    master_user_options {
      master_user_arn = aws_iam_role.lambda_role.arn
    }
  }

  access_policies = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          AWS = aws_iam_role.lambda_role.arn
        }
        Action   = "es:*"
        Resource = "arn:aws:es:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:domain/${var.opensearch_domain}-${var.environment}/*"
      }
    ]
  })

  tags = var.common_tags
}

# DynamoDB Tables
resource "aws_dynamodb_table" "conversation_history" {
  name           = "AaiConversationHistory-${var.environment}"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "session_id"
  range_key      = "timestamp"

  attribute {
    name = "session_id"
    type = "S"
  }

  attribute {
    name = "timestamp"
    type = "N"
  }

  ttl {
    attribute_name = "ttl_epoch"
    enabled        = true
  }

  point_in_time_recovery {
    enabled = true
  }

  tags = var.common_tags
}

resource "aws_dynamodb_table" "support_tickets" {
  name         = "SupportTickets-${var.environment}"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "ticket_id"

  attribute {
    name = "ticket_id"
    type = "S"
  }

  attribute {
    name = "session_id"
    type = "S"
  }

  attribute {
    name = "created_at"
    type = "S"
  }

  global_secondary_index {
    name     = "SessionIndex"
    hash_key = "session_id"
    range_key = "created_at"
    projection_type = "ALL"
  }

  point_in_time_recovery {
    enabled = true
  }

  tags = var.common_tags
}

# S3 Buckets
resource "aws_s3_bucket" "search_results" {
  bucket = "support-agent-search-results-${var.environment}"
  tags   = var.common_tags
}

resource "aws_s3_bucket" "raw_data" {
  bucket = "support-agent-data-${var.environment}"
  tags   = var.common_tags
}

resource "aws_s3_bucket_versioning" "raw_data" {
  bucket = aws_s3_bucket.raw_data.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "raw_data" {
  bucket = aws_s3_bucket.raw_data.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_versioning" "search_results" {
  bucket = aws_s3_bucket.search_results.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "search_results" {
  bucket = aws_s3_bucket.search_results.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# IAM Role for Lambda Functions
resource "aws_iam_role" "lambda_role" {
  name = "AgenticRag-Lambda-Role-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })

  tags = var.common_tags
}

resource "aws_iam_role_policy_attachment" "lambda_basic" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy" "lambda_permissions" {
  name = "AgenticRagPermissions"
  role = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:ListBucket"
        ]
        Resource = [
          "${aws_s3_bucket.search_results.arn}/*",
          aws_s3_bucket.search_results.arn,
          "arn:aws:s3:::support-agent-data-${var.environment}/*",
          "arn:aws:s3:::support-agent-data-${var.environment}"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "textract:StartDocumentTextDetection",
          "textract:GetDocumentTextDetection",
          "textract:StartDocumentAnalysis",
          "textract:GetDocumentAnalysis"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "bedrock:InvokeModel"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "es:ESHttpGet",
          "es:ESHttpPut",
          "es:ESHttpPost",
          "es:DescribeDomain"
        ]
        Resource = "${aws_opensearch_domain.agentic_rag.arn}/*"
      },
      {
        Effect = "Allow"
        Action = "logs:*",
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = "cloudwatch:PutMetricData",
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "dynamodb:Query",
          "dynamodb:PutItem",
          "dynamodb:GetItem",
          "dynamodb:UpdateItem"
        ]
        Resource = [
          aws_dynamodb_table.conversation_history.arn,
          aws_dynamodb_table.support_tickets.arn,
          "${aws_dynamodb_table.support_tickets.arn}/index/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "states:StartExecution",
          "states:StartSyncExecution"
        ]
        Resource = "arn:aws:states:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:stateMachine:*"
      },
      {
        Effect = "Allow"
        Action = [
          "sagemaker:InvokeEndpoint"
        ]
        Resource = [
          "arn:aws:sagemaker:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:endpoint/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "ecr:GetDownloadUrlForLayer",
          "ecr:BatchGetImage",
          "ecr:BatchCheckLayerAvailability"
        ]
        Resource = "arn:aws:ecr:${data.aws_region.current.name}:*:repository/*"
      },
      {
        Effect = "Allow"
        Action = "ecr:GetAuthorizationToken",
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "ses:SendEmail",
          "ses:SendRawEmail"
        ]
        Resource = "*"
      }
    ]
  })
}

# Step Functions Role
resource "aws_iam_role" "step_functions_role" {
  name = "AgenticRag-StepFunctions-Role-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "states.amazonaws.com"
        }
      }
    ]
  })

  tags = var.common_tags
}

resource "aws_iam_role_policy" "step_functions_permissions" {
  name = "StepFunctionsLambdaInvoke"
  role = aws_iam_role.step_functions_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "lambda:InvokeFunction"
        ]
        Resource = "arn:aws:lambda:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:function:aai_*"
      }
    ]
  })
}

# SageMaker Role
resource "aws_iam_role" "sagemaker_role" {
  name = "AgenticRag-SageMaker-Role-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "sagemaker.amazonaws.com"
        }
      }
    ]
  })

  tags = var.common_tags
}

resource "aws_iam_role_policy_attachment" "sagemaker_full_access" {
  role       = aws_iam_role.sagemaker_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSageMakerFullAccess"
}