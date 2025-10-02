# Knowledge Retrieval Agent - Final Results Processor
# Prepares final results and calculates quality metrics

import boto3
import json
import time
from datetime import datetime

s3 = boto3.client('s3')
BUCKET_NAME = 'support-agent-search-results'

def load_candidates_s3(s3_key):
    response = s3.get_object(Bucket=BUCKET_NAME, Key=s3_key)
    return json.loads(response['Body'].read())

def calculate_quality_metrics(results, user_query):
    if not results:
        return {'avg_score': 0, 'score_variance': 0, 'result_count': 0}
    
    scores = [hit[1] for hit in results]
    avg_score = sum(scores) / len(scores)
    variance = sum((x - avg_score) ** 2 for x in scores) / len(scores)
    
    return {
        'avg_score': avg_score,
        'score_variance': variance,
        'result_count': len(results),
        'min_score': min(scores),
        'max_score': max(scores)
    }

def lambda_handler(event, context):
    start_time = time.time()
    cloudwatch = boto3.client('cloudwatch')
    s3 = boto3.client('s3')
    
    query_id = event.get('query_id')
    
    try:
        # Load candidates from S3
        candidates_s3_key = event.get('candidates_s3_key')
        candidates = load_candidates_s3(candidates_s3_key) if candidates_s3_key else event['candidates']
        
        max_results = event.get('max_results', 10)
        user_query = event.get('user_query', '')
        
        # Prepare final results
        final_results = candidates[:max_results]
        chunks = []
        metadata = []
        
        for hit, score in final_results:
            src = hit["_source"]
            chunks.append(src.get("text", ""))
            metadata.append({
                "id": hit["_id"],
                "final_score": score,
                "source": src.get("source"),
                "ticket_id": src.get("ticket_id"),
                "metadata": src.get("metadata", {})
            })
        
        # Calculate quality metrics
        quality_metrics = calculate_quality_metrics(final_results, user_query)
        
        # Aggregate all monitoring data
        all_monitoring = event.get('all_monitoring', [])
        total_time = (time.time() - start_time) * 1000
        
        final_monitoring = {
            'query_id': query_id,
            'stage': 'final_results',
            'timestamp': datetime.utcnow().isoformat(),
            'processing_time_ms': total_time,
            'final_result_count': len(final_results),
            'quality_metrics': quality_metrics,
            'pipeline_stages': all_monitoring
        }
        
        # Store quality data in S3
        quality_data = {
            'query_id': query_id,
            'timestamp': datetime.utcnow().isoformat(),
            'user_query': user_query,
            'parameters': {
                'max_results': max_results,
                'use_reranker': event.get('use_reranker', False),
                'use_mmr': event.get('use_mmr', False)
            },
            'quality_metrics': quality_metrics,
            'pipeline_performance': all_monitoring,
            'results_metadata': metadata
        }
        
        # Store in S3 with date partitioning
        date_prefix = datetime.utcnow().strftime('%Y/%m/%d')
        s3_key = f"rag-quality-metrics/{date_prefix}/{query_id}.json"
        
        s3.put_object(
            Bucket=BUCKET_NAME,
            Key=s3_key,
            Body=json.dumps(quality_data),
            ContentType='application/json'
        )
        
        # Send final metrics to CloudWatch
        cloudwatch.put_metric_data(
            Namespace='RAG/FinalResults',
            MetricData=[
                {'MetricName': 'FinalResultCount', 'Value': len(final_results)},
                {'MetricName': 'AverageScore', 'Value': quality_metrics['avg_score']},
                {'MetricName': 'ScoreVariance', 'Value': quality_metrics['score_variance']},
                {'MetricName': 'ProcessingLatency', 'Value': total_time, 'Unit': 'Milliseconds'}
            ]
        )
        
        return {
            'statusCode': 200,
            'chunks': chunks,
            'metadata': metadata,
            'monitoring': final_monitoring,
            'quality_s3_location': s3_key
        }
        
    except Exception as e:
        error_data = {
            'query_id': query_id,
            'stage': 'final_results',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }
        print(f"ERROR: {json.dumps(error_data)}")
        
        cloudwatch.put_metric_data(
            Namespace='RAG/FinalResults',
            MetricData=[{'MetricName': 'Errors', 'Value': 1}]
        )
        
        return {'statusCode': 500, 'error': str(e), 'monitoring': error_data}