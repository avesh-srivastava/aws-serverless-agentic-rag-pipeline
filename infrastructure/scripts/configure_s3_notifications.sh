#!/bin/bash

# Configure S3 Event Notifications
# This script configures S3 bucket notifications to trigger Lambda functions

set -e

ENVIRONMENT=${1:-dev}
REGION=${2:-ap-south-1}

echo "📬 Configuring S3 Event Notifications - Environment: $ENVIRONMENT"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get AWS Account ID
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# Configuration
RAW_DATA_BUCKET="support-agent-data-$ENVIRONMENT"
INGESTION_LAMBDA_FUNCTION="aai_trigger_step_function_ingestion"
LAMBDA_ARN="arn:aws:lambda:$REGION:$AWS_ACCOUNT_ID:function:$INGESTION_LAMBDA_FUNCTION"

echo -e "${BLUE}📋 Configuration:${NC}"
echo "Bucket: $RAW_DATA_BUCKET"
echo "Lambda: $INGESTION_LAMBDA_FUNCTION"
echo "Lambda ARN: $LAMBDA_ARN"

# Add Lambda permission for S3 to invoke the function
echo -e "${YELLOW}🔐 Adding Lambda permission for S3...${NC}"
aws lambda add-permission \
    --function-name "$INGESTION_LAMBDA_FUNCTION" \
    --principal s3.amazonaws.com \
    --action lambda:InvokeFunction \
    --statement-id "s3-trigger-ingestion-$ENVIRONMENT" \
    --source-arn "arn:aws:s3:::$RAW_DATA_BUCKET" \
    --region "$REGION" 2>/dev/null || echo "  ℹ️  Permission already exists"

# Create notification configuration JSON
NOTIFICATION_CONFIG=$(cat << EOF
{
        "LambdaFunctionConfigurations": [
        {
            "Id": "ingestion-trigger-$ENVIRONMENT",
            "LambdaFunctionArn": "$LAMBDA_ARN",
            "Events": ["s3:ObjectCreated:*"],
            "Filter": {
                "Key": {
                    "FilterRules": [
                        {
                            "Name": "prefix",
                            "Value": "raw/"
                        }
                    ]
                }
            }
        }
    ]
}
EOF
)

# Configure S3 bucket notification
echo -e "${YELLOW}📬 Configuring S3 bucket notification...${NC}"

aws s3api put-bucket-notification-configuration \
    --bucket "$RAW_DATA_BUCKET" \
    --notification-configuration "$NOTIFICATION_CONFIG" \
    --region "$REGION"

echo -e "${GREEN}✅ S3 event notification configured successfully!${NC}"
echo -e "${BLUE}📋 Summary:${NC}"
echo "• Bucket: $RAW_DATA_BUCKET"
echo "• Trigger: s3:ObjectCreated:* (prefix: raw/)"
echo "• Lambda: $INGESTION_LAMBDA_FUNCTION"
echo "• Files uploaded to s3://$RAW_DATA_BUCKET/raw/ will automatically trigger the ingestion pipeline"