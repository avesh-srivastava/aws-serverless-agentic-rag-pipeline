# Knowledge Retrieval Agent - MMR Diversity Filter
# Applies Maximal Marginal Relevance for result diversification

import boto3
import json
import time
from datetime import datetime
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

def load_candidates_s3(s3_key):
    response = s3.get_object(Bucket=BUCKET_NAME, Key=s3_key)
    return json.loads(response['Body'].read())

def cosine_similarity(a, b):
    """Simple cosine similarity"""
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = sum(x * x for x in a) ** 0.5
    norm_b = sum(x * x for x in b) ** 0.5
    return dot / (norm_a * norm_b) if norm_a and norm_b else 0

def simple_mmr(candidates, query_embedding, top_k=10):
    """Simplified MMR with cosine similarity"""
    if len(candidates) <= top_k:
        return candidates
    
    selected = []
    remaining = list(candidates)
    
    while remaining and len(selected) < top_k:
        best_idx = 0
        best_score = -1
        
        for i, (hit, score) in enumerate(remaining):
            # Get embedding, use zeros if missing
            emb = hit['_source'].get('embedding', [0.0] * 1536)
            
            # Relevance to query
            relevance = cosine_similarity(query_embedding, emb)
            
            # Penalty for similarity to selected items
            max_sim = 0
            if selected:
                for sel_hit, _ in selected:
                    sel_emb = sel_hit['_source'].get('embedding', [0.0] * 1536)
                    sim = cosine_similarity(emb, sel_emb)
                    max_sim = max(max_sim, sim)
            
            # MMR score: relevance - diversity penalty
            mmr_score = 0.7 * relevance - 0.3 * max_sim
            
            if mmr_score > best_score:
                best_score = mmr_score
                best_idx = i
        
        selected.append(remaining.pop(best_idx))
    
    return selected

def lambda_handler(event, context):
    start_time = time.time()
    cloudwatch = boto3.client('cloudwatch')
    
    query_id = event.get('query_id')
    
    try:
        if not event.get('use_mmr', False):
            # Pass through S3 key without processing
            return {
                'statusCode': 200,
                'candidates_s3_key': event.get('candidates_s3_key'),
                'monitoring': {
                    'query_id': query_id,
                    'stage': 'mmr',
                    'enabled': False,
                    'timestamp': datetime.utcnow().isoformat()
                }
            }
        
        # Load candidates from S3
        candidates_s3_key = event.get('candidates_s3_key')
        candidates = load_candidates_s3(candidates_s3_key) if candidates_s3_key else event['candidates']
        
        max_results = event.get('max_results', 10)
        
        query_embedding = event.get('queryEmbedding', [])
        
        # Apply MMR
        mmr_start = time.time()
        mmr_results = simple_mmr(candidates, query_embedding, max_results)
        mmr_time = (time.time() - mmr_start) * 1000
        
        # Monitoring
        monitoring = {
            'query_id': query_id,
            'stage': 'mmr',
            'enabled': True,
            'timestamp': datetime.utcnow().isoformat(),
            'mmr_time_ms': mmr_time,
            'total_time_ms': (time.time() - start_time) * 1000,
            'relevance_weight': 0.7,
            'input_count': len(candidates),
            'output_count': len(mmr_results)
        }
        
        # Store results in S3
        results_s3_key = store_candidates_s3(mmr_results, query_id, 'mmr')
        
        # Send metrics immediately
        cloudwatch.put_metric_data(
            Namespace='RAG/MMR',
            MetricData=[
                {'MetricName': 'MMRLatency', 'Value': mmr_time, 'Unit': 'Milliseconds'},
                {'MetricName': 'DiversityReduction', 'Value': len(candidates) - len(mmr_results)}
            ]
        )
        
        return {
            'statusCode': 200,
            'candidates_s3_key': results_s3_key,
            'monitoring': monitoring
        }
        
    except Exception as e:
        error_data = {
            'query_id': query_id,
            'stage': 'mmr',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }
        print(f"ERROR: {json.dumps(error_data)}")
        
        cloudwatch.put_metric_data(
            Namespace='RAG/MMR',
            MetricData=[{'MetricName': 'Errors', 'Value': 1}]
        )
        
        return {'statusCode': 500, 'error': str(e), 'monitoring': error_data}