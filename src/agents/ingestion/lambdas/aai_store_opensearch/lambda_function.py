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
    region = os.environ.get("AWS_REGION", "ap-south-1")
    service = 'es'
    
    print(f"Environment variables: host={host}, index_name={index_name}, region={region}")
    
    if not host or not index_name:
        return {
            'statusCode': 400,
            'body': f'Missing required environment variables: OPENSEARCH_DOMAIN={host}, OPENSEARCH_INDEX={index_name}'
        }
    
    bucket = event.get("bucket")
    embedding_keys = event.get("embeddingKeys", [])
    
    if not bucket or not embedding_keys:
        return {
            'statusCode': 400,
            'body': f'Missing required event parameters: bucket={bucket}, embeddingKeys={embedding_keys}'
        }
    
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
            
            processed_count = 0
            skipped_count = 0
            
            for i, item in enumerate(embedding_data["embeddings"]):
                try:
                    # Skip items with null, empty, or invalid embeddings
                    embedding = item.get("embedding")
                    if embedding is None or embedding == "null" or not embedding or len(embedding) == 0:
                        print(f"Skipping item {i} with invalid embedding: {item.get('text', 'Unknown')[:50]}...")
                        skipped_count += 1
                        continue
                    
                    # Validate embedding is a list of numbers
                    if not isinstance(embedding, list) or not all(isinstance(x, (int, float)) for x in embedding):
                        print(f"Skipping item {i} with invalid embedding format: {type(embedding)}")
                        skipped_count += 1
                        continue
                        
                    doc = {
                        "embedding": embedding,
                        "text": item.get("text", ""),
                        "source": item.get("source", "")
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
                    
                    # Index the document
                    try:
                        response = opensearch.index(index=index_name, body=doc)
                        processed_count += 1
                        print(f"Successfully indexed document {i}: {response.get('_id', 'unknown')}")
                    except Exception as index_error:
                        print(f"OpenSearch indexing error for item {i}: {str(index_error)}")
                        print(f"Document structure: embedding_len={len(embedding)}, text_len={len(doc.get('text', ''))}, source={doc.get('source', '')}")
                        skipped_count += 1
                        continue
                    
                except Exception as e:
                    print(f"Error processing item {i}: {str(e)}")
                    print(f"Item keys: {list(item.keys()) if isinstance(item, dict) else 'not a dict'}")
                    skipped_count += 1
                    continue
            
            print(f"Processing complete: {processed_count} indexed, {skipped_count} skipped")
        
        return {"status": "stored"}

    except Exception as e:
        return {
            'statusCode': 500,
            'body': str(e)
        }
