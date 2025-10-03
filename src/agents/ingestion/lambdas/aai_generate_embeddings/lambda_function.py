import boto3
import json
import os
import time
from botocore.exceptions import ClientError

region = os.environ.get("AWS_REGION")

bedrock = boto3.client('bedrock-runtime', region_name=region)
s3 = boto3.client("s3")
embed_model = os.environ.get("EMBED_MODEL")

def get_embedding(text):
    max_retries = 3
    base_delay = 1
    
    for attempt in range(max_retries):
        try:
            body = json.dumps({"inputText": text})
            resp = bedrock.invoke_model(
                modelId=embed_model,
                body=body
            )
            result = json.loads(resp['body'].read())
            return result['embedding']
        except ClientError as e:
            if e.response['Error']['Code'] == 'ThrottlingException' and attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt)
                time.sleep(delay)
                continue
            raise e

def lambda_handler(event, context):
    bucket = event["bucket"]
    batch_id = event["batchId"]
    filename = os.path.splitext(os.path.basename(event["filename"]))[0]
    embeddings = []

    for chunk_key in event["chunkKeys"]:
        obj = s3.get_object(Bucket=bucket, Key=chunk_key)
        chunk_data = json.loads(obj["Body"].read())
        embedding = get_embedding(chunk_data["text"])
        
        # Base embedding object
        embedding_obj = {
            "embedding": embedding, 
            "text": chunk_data["text"], 
            "source": chunk_data["source"]
        }
        
        # Add additional fields if they exist (for CSV files)
        for field in ["ticket_id", "metadata", "created_at"]:
            if field in chunk_data:
                embedding_obj[field] = chunk_data[field]
        
        embeddings.append(embedding_obj)
        time.sleep(0.2)  # Small delay between calls

    # Create a clean batch ID from timestamp
    clean_batch_id = batch_id.replace(":", "-").replace(".", "-")
    embeddings_key = f"processed/embeddings/{filename}_batch_{clean_batch_id}.json"
    s3.put_object(
        Bucket=bucket,
        Key=embeddings_key,
        Body=json.dumps({"embeddings": embeddings})
    )

    return {"embeddingsKey": embeddings_key}
