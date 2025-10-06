# Knowledge Retrieval Agent - Cross-Encoder Reranking
# Reranks search results using SageMaker cross-encoder model

import boto3
import json
import os
import time
from datetime import datetime

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

def load_candidates_s3(s3_key):
    response = s3.get_object(Bucket=BUCKET_NAME, Key=s3_key)
    return json.loads(response['Body'].read())

def lambda_handler(event, context):
    start_time = time.time()
    cloudwatch = boto3.client('cloudwatch')
    
    query_id = event.get('query_id')
    
    try:
        if not event.get('use_reranker', False):
            return {
                'statusCode': 200,
                'candidates_s3_key': event.get('candidates_s3_key'),
                'monitoring': {
                    'query_id': query_id,
                    'stage': 'cross_encoder',
                    'enabled': False,
                    'timestamp': datetime.utcnow().isoformat()
                }
            }
        
        # Load candidates from S3
        candidates_s3_key = event.get('candidates_s3_key')
        candidates = load_candidates_s3(candidates_s3_key) if candidates_s3_key else event['candidates']
        
        sagemaker = boto3.client('sagemaker-runtime')
        user_query = event['user_query']
        
        # Prepare query-document pairs in correct format
        pairs = [{
            "text": user_query,
            "text_pair": hit[0]['_source']['text']
        } for hit in candidates]
        
        # Get endpoint from environment
        sagemaker_endpoint = os.environ.get('SAGEMAKER_ENDPOINT', "minilm-reranker-1756624753")
        if not sagemaker_endpoint:
            raise Exception('SAGEMAKER_ENDPOINT environment variable not set')
        
        # Call SageMaker endpoint
        rerank_start = time.time()
        response = sagemaker.invoke_endpoint(
            EndpointName=sagemaker_endpoint,
            ContentType='application/json',
            Body=json.dumps({"inputs": pairs})
        )
        
        scores_response = json.loads(response['Body'].read().decode())
        
        # Extract scores from SageMaker response format
        # scores returned from SageMaker are dictionaries (with labels and scores) rather than simple numeric values
        if isinstance(scores_response[0], dict):
            # Handle format like [{'label': 'LABEL_1', 'score': 0.95}, ...]
            scores = [item['score'] if 'score' in item else item.get('LABEL_1', 0) for item in scores_response]
        else:
            # Handle simple numeric array
            scores = scores_response
        
        reranked = [(candidates[i][0], scores[i]) for i in range(len(candidates))]
        reranked = sorted(reranked, key=lambda x: x[1], reverse=True)
        rerank_time = (time.time() - rerank_start) * 1000
        
        # Monitoring
        monitoring = {
            'query_id': query_id,
            'stage': 'cross_encoder',
            'enabled': True,
            'timestamp': datetime.utcnow().isoformat(),
            'rerank_time_ms': rerank_time,
            'total_time_ms': (time.time() - start_time) * 1000,
            'input_count': len(candidates),
            'output_count': len(reranked)
        }
        
        # Send metrics immediately
        cloudwatch.put_metric_data(
            Namespace='RAG/CrossEncoder',
            MetricData=[
                {'MetricName': 'RerankLatency', 'Value': rerank_time, 'Unit': 'Milliseconds'},
                {'MetricName': 'CandidatesProcessed', 'Value': len(candidates)}
            ]
        )
        
        # Store reranked results in S3
        results_s3_key = store_candidates_s3(reranked, query_id, 'cross_encoder')
        
        return {
            'statusCode': 200,
            'candidates_s3_key': results_s3_key,
            'monitoring': monitoring
        }
        
    except Exception as e:
        error_data = {
            'query_id': query_id,
            'stage': 'cross_encoder',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }
        print(f"ERROR: {json.dumps(error_data)}")
        
        cloudwatch.put_metric_data(
            Namespace='RAG/CrossEncoder',
            MetricData=[{'MetricName': 'Errors', 'Value': 1}]
        )
        
        return {'statusCode': 500, 'error': str(e), 'monitoring': error_data}