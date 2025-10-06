# Conversation Agent - Conversation Storage
# Stores conversation history in DynamoDB

import os, json, time, boto3, ast
from decimal import Decimal

TABLE = os.environ.get("CONVERSATION_TABLE","AaiConversationHistory")
ddb = boto3.resource("dynamodb")
table = ddb.Table(TABLE)

def lambda_handler(event, context):
    session_id = event.get("session_id")
    user_query = event.get("user_query")
    sources = event.get("sources", [])

    # Parse the stringified Python dict safely
    raw_response = event.get("agent_response")

    if not session_id or not user_query or not raw_response:
        return {"status":"error","message":"Missing session_id/user_query/agent_response"}

    try:
        response_data = ast.literal_eval(raw_response)
    except Exception as e:
        print(f"Error parsing agent_response: {e}")
        response_data = {}

    # Extract values
    input_token_count = response_data.get("inputTextTokenCount")
    results = response_data.get("results", [])
    
    if results:
        output_token_count = results[0].get("tokenCount")
        output_text = results[0].get("outputText")
        completion_reason = results[0].get("completionReason")
    else:
        output_token_count = None
        output_text = None
        completion_reason = None

    # Convert final_score to Decimal for DynamoDB
    for source in sources:
        if isinstance(source.get('final_score'), float):
            source['final_score'] = Decimal(str(source['final_score']))
    
    now_ms = int(time.time()*1000)
    item = {
        "session_id": session_id,
        "timestamp": now_ms,
        "user_query": user_query,
        "agent_response": output_text,
        "sources": sources,
        "input_token_count": input_token_count,
        "output_token_count": output_token_count,
        "completion_reason": completion_reason
    }

    # Optional TTL: expire after N days
    ttl_days = int(os.environ.get("TTL_DAYS","7"))
    if ttl_days > 0:
        item["ttl_epoch"] = int(time.time()) + ttl_days*24*3600

    table.put_item(Item=item)

    return {
        "statusCode": 200,
        "message": "Memory stored successfully",
        "stored_at": now_ms
    }
