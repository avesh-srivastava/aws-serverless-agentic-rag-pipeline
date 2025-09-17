import boto3
import textwrap
import json
import os

s3 = boto3.client('s3')
CHUNK_BATCH_SIZE = int(os.environ.get("CHUNK_BATCH_SIZE", "20"))

def batch_chunks(chunk_keys, batch_size=CHUNK_BATCH_SIZE):
    return [chunk_keys[i:i + batch_size] for i in range(0, len(chunk_keys), batch_size)]

def lambda_handler(event, context):
    bucket = event["Payload"]["bucket"]
    text_key = event["Payload"]["textKey"]

    raw_text = s3.get_object(Bucket=bucket, Key=text_key)["Body"].read().decode("utf-8")
    chunks = textwrap.wrap(raw_text, 1000)  # chunk size ~1000 chars

    chunk_objects = []
    for idx, chunk in enumerate(chunks):
        chunk_data = {"source": text_key, "chunk_id": idx, "text": chunk}
        chunk_key = text_key.replace("processed/text/", "processed/chunks/") + f"_{idx}.json"
        s3.put_object(Body=json.dumps(chunk_data), Bucket=bucket, Key=chunk_key)
        chunk_objects.append(chunk_key)

    chunk_batches = batch_chunks(chunk_objects)
    return {"chunkBatches": chunk_batches, "bucket": bucket}
