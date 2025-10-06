#!/bin/bash

# Deploy Lambda Functions Only
# Simple wrapper for Terraform targeting

set -e

ENVIRONMENT=${1:-dev}
AWS_REGION=${2:-ap-south-1}

echo "Deploying Lambda functions only for environment: $ENVIRONMENT"

cd infrastructure/terraform

terraform apply \
    -target=aws_lambda_function.agentic_rag_functions \
    -var="environment=$ENVIRONMENT" \
    -var="aws_region=$AWS_REGION" \
    -auto-approve

echo "Lambda functions deployed successfully!"