import boto3
import json
import time
from datetime import datetime
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth
import os

def lambda_handler(event, context):
    # OpenSearch domain endpoint - replace with your actual endpoint
    host = os.environ.get("OPENSEARCH_DOMAIN")
    index_name = os.environ.get("OPENSEARCH_INDEX")
    region = os.environ.get("AWS_REGION")
    service = 'es'
    bucket = event["bucket"]
    embedding_keys = event["embeddingKeys"]
    s3 = boto3.client("s3")
    
    # Get credentials from the AWS SDK
    credentials = boto3.Session().get_credentials()
    awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, 
                       region, service, session_token=credentials.token)
    
    # Create the OpenSearch client
    opensearch = OpenSearch(
        hosts = [{'host': host, 'port': 443}],
        http_auth = awsauth,
        use_ssl = True,
        verify_certs = True,
        connection_class = RequestsHttpConnection
    )
    
    # Read and store embeddings from S3 files
    try:
        for embedding_key in embedding_keys:
            obj = s3.get_object(Bucket=bucket, Key=embedding_key)
            embedding_data = json.loads(obj["Body"].read())
            
            for item in embedding_data["embeddings"]:
                doc = {
                    "embedding": item["embedding"],
                    "text": item["text"],
                    "source": item["source"]
                }
                
                # Add additional fields if they exist
                for field in ["ticket_id", "metadata"]:
                    if field in item:
                        doc[field] = item[field]
                
                # Add created_at if not present
                if "created_at" in item:
                    doc["created_at"] = item["created_at"]
                else:
                    doc["created_at"] = datetime.utcnow().isoformat()
                
                opensearch.index(index=index_name, body=doc)
        
        return {"status": "stored"}

    except Exception as e:
        return {
            'statusCode': 500,
            'body': str(e)
        }
