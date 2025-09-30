import boto3
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth
import os

def lambda_handler(event, context):
    # OpenSearch domain endpoint - replace with your actual endpoint
    host = os.environ.get("OPENSEARCH_DOMAIN")
    index_name = os.environ.get("OPENSEARCH_INDEX")
    region = os.environ.get("AWS_REGION")
    service = 'es'
    
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
        #Delete index if it exists
        if opensearch.indices.exists(index=index_name):
            opensearch.indices.delete(index=index_name)
        
        # Create index with proper mapping for knn_vector
        index_body = {
            "settings": {
                "index": {
                    "number_of_shards": 1,
                    "number_of_replicas": 0,
                    "knn": True,
                    "similarity": {
                        "default": {
                            "type": "BM25",
                            "k1": 1.2, #Custom BM25 parameters: k1=1.2, b=0.75 (standard optimal values)
                            "b": 0.75
                        }
                    }
                },
                "analysis": {
                    "analyzer": { #Enhanced analyzer: Custom English analyzer with stemming, stop words, and lowercasing
                        "english_bm25": {
                            "type": "custom",
                            "tokenizer": "standard",
                            "filter": [
                                "lowercase",
                                "stop",
                                "snowball" #Text processing: Snowball stemmer for better term matching
                            ]
                        }
                    }
                }
            },
            "mappings": {
                "properties": {
                    "embedding": {
                        "type": "knn_vector",
                        "dimension": 1536,
                        "method": {
                            "name": "hnsw",
                            "space_type": "l2",
                            "engine": "nmslib"
                        }
                    },
                    "text": {
                        "type": "text", #Explicit similarity: Applied BM25 similarity to the text field
                        "analyzer": "english_bm25",
                        "similarity": "default"
                    },
                    "source": {"type": "keyword"},
                    "ticket_id": {"type": "keyword"},
                    "created_at": {"type": "date"},
                    "metadata": {
                        "properties": {
                            "product_purchased": {"type": "keyword"},
                            "type": {"type": "keyword"},
                            "priority": {"type": "keyword"},
                            "channel": {"type": "keyword"},
                            "status": {"type": "keyword"}
                        }
                    }
                }
            }
        }

        opensearch.indices.create(index=index_name, body=index_body)
        print(f"Index {index_name} created successfully")
        
        return {"status": "Index Created"}

    except Exception as e:
        return {
            'statusCode': 500,
            'body': str(e)
        }
