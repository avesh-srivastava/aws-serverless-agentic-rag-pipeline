# Orchestration Agent - Step Function Trigger
# Entry point that triggers the RAG pipeline orchestration on a new file upload to S3 bucket

import json
import boto3
import os

sf_client = boto3.client('stepfunctions')
state_machine_arn = os.environ.get('STEP_FUNCTION_INGESTION_ARN')

def lambda_handler(event, context):
    # Extract basic info (you can enrich or simplify as needed)
    record = event['Records'][0]
    bucket = record['s3']['bucket']['name']
    key = record['s3']['object']['key']
    file_ext = key.split('.')[-1].lower()

    input_data = {
        "bucket": bucket,
        "key": key,
        "fileExtension": f".{file_ext}"
    }

    # Start Step Function execution
    response = sf_client.start_execution(
        stateMachineArn=state_machine_arn,
        input=json.dumps(input_data)
    )

    print("Started Step Function:", response['executionArn'])
    return {"status": "triggered"}
