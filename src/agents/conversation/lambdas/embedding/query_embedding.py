# Conversation Agent - Query Embedding
# Generates embeddings for user queries using Bedrock

# lambda_get_query_embedding.py
import os, json, boto3
bedrock = boto3.client("bedrock-runtime")  # ensure region and permissions

EMBED_MODEL = os.environ.get("EMBED_MODEL", "amazon.titan-embed-text-v1")

def lambda_handler(event, context):
    user_query = event.get("user_query", "")
    if not user_query:
        raise ValueError("Missing user_query")

    payload = json.dumps({"inputText": user_query})
    resp = bedrock.invoke_model(modelId=EMBED_MODEL, body=payload)
    body = resp['body'].read()
    result = json.loads(body)
    embedding = result.get("embedding")  # list[float]

    return {"embedding": embedding}
