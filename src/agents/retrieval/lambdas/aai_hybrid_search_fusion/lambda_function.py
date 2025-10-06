# Knowledge Retrieval Agent - Hybrid Search
# Performs BM25 and kNN search with RRF fusion

import boto3
import json
import time
from datetime import datetime
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth
from collections import defaultdict
import os

s3 = boto3.client('s3')
BUCKET_NAME = os.environ.get("SEARCH_RESULTS_BUCKET", "support-agent-search-results-dev")

def store_candidates_s3(candidates, query_id, stage):
    key = f"candidates/{query_id}/{stage}.json"
    s3.put_object(
        Bucket=BUCKET_NAME,
        Key=key,
        Body=json.dumps(candidates),
        ContentType='application/json'
    )
    return key

def rrf_fusion(bm25_results, knn_results, k=60):
    scores = defaultdict(float)
    doc_data = {}
    
    for rank, hit in enumerate(bm25_results, 1):
        doc_id = hit['_id']
        scores[doc_id] += 1 / (k + rank)
        doc_data[doc_id] = hit
    
    for rank, hit in enumerate(knn_results, 1):
        doc_id = hit['_id']
        scores[doc_id] += 1 / (k + rank)
        if doc_id not in doc_data:
            doc_data[doc_id] = hit
    
    sorted_docs = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return [(doc_data[doc_id], score) for doc_id, score in sorted_docs]

def lambda_handler(event, context):
    start_time = time.time()
    cloudwatch = boto3.client('cloudwatch')
    host = os.environ.get("OPENSEARCH_DOMAIN")
    index_name = os.environ.get("OPENSEARCH_INDEX")
    region = os.environ.get("AWS_REGION")
    service = 'es'
    
    query_id = event.get('query_id', f"query_{int(time.time())}")
    
    try:
        # OpenSearch setup
        credentials = boto3.Session().get_credentials()
        awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, 
                           region, service, session_token=credentials.token)
        
        opensearch = OpenSearch(
            hosts=[{'host': host, 'port': 443}],
            http_auth=awsauth,
            use_ssl=True,
            verify_certs=True,
            connection_class=RequestsHttpConnection
        )
        
        # Build queries
        max_results = event.get('max_results', 10)
        user_query = event['user_query']
        query_embedding = event['queryEmbedding']
        product_filter = event.get('product_filter')
        
        bm25_query = {
            "size": max_results,
            "query": {
                "bool": {
                    "must": [{"match": {"text": user_query}}]
                }
            }
        }
        
        knn_query = {
            "size": max_results,
            "query": {
                "knn": {
                    "embedding": {
                        "vector": query_embedding,
                        "k": max_results
                    }
                }
            }
        }
        
        # Add product filter if specified
        if product_filter:
            bm25_query["query"]["bool"]["filter"] = [{"term": {"metadata.product_purchased": product_filter}}]
            knn_query["query"] = {
                "bool": {
                    "must": [knn_query["query"]],
                    "filter": [{"term": {"metadata.product_purchased": product_filter}}]
                }
            }
        
        # Execute searches
        bm25_start = time.time()
        bm25_resp = opensearch.search(index=index_name, body=bm25_query)
        bm25_time = (time.time() - bm25_start) * 1000
        
        knn_start = time.time()
        knn_resp = opensearch.search(index=index_name, body=knn_query)
        knn_time = (time.time() - knn_start) * 1000
        
        # RRF Fusion
        rrf_start = time.time()
        fused_results = rrf_fusion(bm25_resp["hits"]["hits"], knn_resp["hits"]["hits"])
        rrf_time = (time.time() - rrf_start) * 1000
        
        # Monitoring data
        monitoring = {
            'query_id': query_id,
            'stage': 'search_fusion',
            'timestamp': datetime.utcnow().isoformat(),
            'bm25_time_ms': bm25_time,
            'knn_time_ms': knn_time,
            'rrf_time_ms': rrf_time,
            'total_time_ms': (time.time() - start_time) * 1000,
            'bm25_results': len(bm25_resp["hits"]["hits"]),
            'knn_results': len(knn_resp["hits"]["hits"]),
            'fused_results': len(fused_results)
        }
        
        # Send metrics to CloudWatch immediately
        cloudwatch.put_metric_data(
            Namespace='RAG/SearchFusion',
            MetricData=[
                {'MetricName': 'BM25Latency', 'Value': bm25_time, 'Unit': 'Milliseconds'},
                {'MetricName': 'KNNLatency', 'Value': knn_time, 'Unit': 'Milliseconds'},
                {'MetricName': 'RRFLatency', 'Value': rrf_time, 'Unit': 'Milliseconds'}
            ]
        )
        
        # Store candidates in S3
        final_candidates = fused_results[:event.get('max_results', 10) * 2]
        candidates_s3_key = store_candidates_s3(final_candidates, query_id, 'search_fusion')
        
        return {
            'statusCode': 200,
            'candidates_s3_key': candidates_s3_key,
            'monitoring': monitoring
        }
        
    except Exception as e:
        # Log error immediately
        error_data = {
            'query_id': query_id,
            'stage': 'search_fusion',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }
        print(f"ERROR: {json.dumps(error_data)}")
        
        cloudwatch.put_metric_data(
            Namespace='RAG/SearchFusion',
            MetricData=[{'MetricName': 'Errors', 'Value': 1}]
        )
        
        return {'statusCode': 500, 'error': str(e), 'monitoring': error_data}