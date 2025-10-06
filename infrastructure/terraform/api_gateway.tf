# API Gateway Configuration
# REST API for the Agentic RAG system

# API Gateway REST API
resource "aws_api_gateway_rest_api" "agentic_rag_api" {
  name        = "agentic-rag-api-${var.environment}"
  description = "Agentic RAG Pipeline API"
  
  endpoint_configuration {
    types = ["REGIONAL"]
  }

  tags = var.common_tags
}

# API Gateway Resource for /getanswers
resource "aws_api_gateway_resource" "getanswers" {
  rest_api_id = aws_api_gateway_rest_api.agentic_rag_api.id
  parent_id   = aws_api_gateway_rest_api.agentic_rag_api.root_resource_id
  path_part   = "getanswers"
}

# API Gateway Method (POST /getanswers)
resource "aws_api_gateway_method" "getanswers_post" {
  rest_api_id   = aws_api_gateway_rest_api.agentic_rag_api.id
  resource_id   = aws_api_gateway_resource.getanswers.id
  http_method   = "POST"
  authorization = "NONE"

  request_validator_id = aws_api_gateway_request_validator.getanswers_validator.id
  
  request_models = {
    "application/json" = aws_api_gateway_model.getanswers_request.name
  }
}

# Request Validator
resource "aws_api_gateway_request_validator" "getanswers_validator" {
  name                        = "getanswers-validator"
  rest_api_id                = aws_api_gateway_rest_api.agentic_rag_api.id
  validate_request_body      = true
  validate_request_parameters = false
}

# Request Model
resource "aws_api_gateway_model" "getanswers_request" {
  rest_api_id  = aws_api_gateway_rest_api.agentic_rag_api.id
  name         = "GetAnswersRequest"
  content_type = "application/json"

  schema = jsonencode({
    "$schema" = "http://json-schema.org/draft-04/schema#"
    title     = "Get Answers Request Schema"
    type      = "object"
    properties = {
      user_query = {
        type        = "string"
        description = "The user's question"
      }
      max_results = {
        type        = "integer"
        minimum     = 1
        maximum     = 50
        description = "Maximum number of results to return"
      }
      product_filter = {
        type        = "string"
        description = "Filter results by product (optional)"
      }
      use_reranker = {
        type        = "boolean"
        description = "Whether to use cross-encoder reranking"
      }
      use_mmr = {
        type        = "boolean"
        description = "Whether to use MMR diversity filtering"
      }
      mmr_lambda = {
        type        = "number"
        minimum     = 0
        maximum     = 1
        description = "MMR lambda parameter for diversity vs relevance"
      }
    }
    required = ["user_query"]
  })
}

# Lambda Integration
resource "aws_api_gateway_integration" "getanswers_lambda" {
  rest_api_id = aws_api_gateway_rest_api.agentic_rag_api.id
  resource_id = aws_api_gateway_resource.getanswers.id
  http_method = aws_api_gateway_method.getanswers_post.http_method

  integration_http_method = "POST"
  type                   = "AWS_PROXY"
  uri                    = aws_lambda_function.agentic_rag_functions["aai_trigger_step_function_retrieval"].invoke_arn
}

# Lambda Permission for API Gateway
resource "aws_lambda_permission" "api_gateway_invoke_retrieval" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.agentic_rag_functions["aai_trigger_step_function_retrieval"].function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.agentic_rag_api.execution_arn}/*/*"
}

# Method Response
resource "aws_api_gateway_method_response" "getanswers_200" {
  rest_api_id = aws_api_gateway_rest_api.agentic_rag_api.id
  resource_id = aws_api_gateway_resource.getanswers.id
  http_method = aws_api_gateway_method.getanswers_post.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin"  = true
    "method.response.header.Access-Control-Allow-Headers" = true
    "method.response.header.Access-Control-Allow-Methods" = true
  }

  response_models = {
    "application/json" = "Empty"
  }
}

# Integration Response
resource "aws_api_gateway_integration_response" "getanswers_200" {
  rest_api_id = aws_api_gateway_rest_api.agentic_rag_api.id
  resource_id = aws_api_gateway_resource.getanswers.id
  http_method = aws_api_gateway_method.getanswers_post.http_method
  status_code = aws_api_gateway_method_response.getanswers_200.status_code

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin"  = "'*'"
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'"
    "method.response.header.Access-Control-Allow-Methods" = "'POST,OPTIONS'"
  }

  depends_on = [aws_api_gateway_integration.getanswers_lambda]
}

# CORS OPTIONS Method
resource "aws_api_gateway_method" "getanswers_options" {
  rest_api_id   = aws_api_gateway_rest_api.agentic_rag_api.id
  resource_id   = aws_api_gateway_resource.getanswers.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "getanswers_options" {
  rest_api_id = aws_api_gateway_rest_api.agentic_rag_api.id
  resource_id = aws_api_gateway_resource.getanswers.id
  http_method = aws_api_gateway_method.getanswers_options.http_method

  type = "MOCK"
  request_templates = {
    "application/json" = jsonencode({
      statusCode = 200
    })
  }
}

resource "aws_api_gateway_method_response" "getanswers_options_200" {
  rest_api_id = aws_api_gateway_rest_api.agentic_rag_api.id
  resource_id = aws_api_gateway_resource.getanswers.id
  http_method = aws_api_gateway_method.getanswers_options.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin"  = true
    "method.response.header.Access-Control-Allow-Headers" = true
    "method.response.header.Access-Control-Allow-Methods" = true
  }
}

resource "aws_api_gateway_integration_response" "getanswers_options_200" {
  rest_api_id = aws_api_gateway_rest_api.agentic_rag_api.id
  resource_id = aws_api_gateway_resource.getanswers.id
  http_method = aws_api_gateway_method.getanswers_options.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin"  = "'*'"
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'"
    "method.response.header.Access-Control-Allow-Methods" = "'POST,OPTIONS'"
  }

  depends_on = [aws_api_gateway_integration.getanswers_options]
}

# API Gateway Deployment
resource "aws_api_gateway_deployment" "agentic_rag_deployment" {
  rest_api_id = aws_api_gateway_rest_api.agentic_rag_api.id

  depends_on = [
    aws_api_gateway_method.getanswers_post,
    aws_api_gateway_method.getanswers_options,
    aws_api_gateway_integration.getanswers_lambda,
    aws_api_gateway_integration.getanswers_options
  ]

  lifecycle {
    create_before_destroy = true
  }
}

# API Gateway Stage
resource "aws_api_gateway_stage" "agentic_rag_stage" {
  deployment_id = aws_api_gateway_deployment.agentic_rag_deployment.id
  rest_api_id   = aws_api_gateway_rest_api.agentic_rag_api.id
  stage_name    = var.environment

  tags = var.common_tags
}