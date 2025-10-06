@echo off
REM Deploy Lambda Functions Script for Windows
REM This script deploys all Lambda functions with proper environment variables

setlocal enabledelayedexpansion

set ENVIRONMENT=%1
set AWS_REGION=%2

if "%ENVIRONMENT%"=="" set ENVIRONMENT=dev
if "%AWS_REGION%"=="" set AWS_REGION=ap-south-1

echo Deploying Lambda functions for environment: %ENVIRONMENT% in region: %AWS_REGION%

REM Change to terraform directory
cd /d "%~dp0..\terraform"

REM Initialize Terraform if needed
if not exist ".terraform" (
    echo Initializing Terraform...
    terraform init
)

REM Plan and apply Lambda function changes
echo Planning Lambda function deployment...
terraform plan -target=aws_lambda_function.agentic_rag_functions -var="environment=%ENVIRONMENT%" -var="aws_region=%AWS_REGION%"

echo Applying Lambda function deployment...
terraform apply -target=aws_lambda_function.agentic_rag_functions -var="environment=%ENVIRONMENT%" -var="aws_region=%AWS_REGION%" -auto-approve

echo Lambda functions deployed successfully!

REM Output function names and ARNs
echo Deployed Lambda functions:
terraform output lambda_function_names

pause