# Data Ingestion Agent - Textract Starter
# Initiates PDF text extraction using AWS Textract

import boto3

textract = boto3.client('textract')

def lambda_handler(event, context):
    bucket = event['bucket']
    key = event['key']

    # For large documents with LAYOUT/TABLES
    response = textract.start_document_analysis(
        DocumentLocation={'S3Object': {'Bucket': bucket, 'Name': key}},
        FeatureTypes=['LAYOUT', 'TABLES']
    )

    # Print response
    print(response)

    # Return response with JobId and S3 location
    return {
        "jobId": response["JobId"],
        "bucket": bucket,
        "key": key
    }
