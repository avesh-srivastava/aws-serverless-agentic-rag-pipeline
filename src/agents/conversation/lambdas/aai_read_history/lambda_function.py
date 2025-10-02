# Conversation Agent - History Reader
# Retrieves conversation history from DynamoDB

# lambda_memory_read.py
import os, json, time, boto3
from boto3.dynamodb.conditions import Key

TABLE = os.environ.get("DDB_TABLE","AaiConversationHistory")
MAX_TURNS = int(os.environ.get("MAX_TURNS","5"))  # total items to return (user+assistant pairs)

ddb = boto3.resource("dynamodb")
table = ddb.Table(TABLE)

def lambda_handler(event, context):
    session_id = event.get("session_id")
    limit = int(event.get("limit", MAX_TURNS))
    if not session_id:
        return {"history": []}

    resp = table.query(
        KeyConditionExpression=Key("session_id").eq(session_id),
        ScanIndexForward=False,  # newest first
        Limit=limit
    )
    items = resp.get("Items", [])
    # reverse to oldest->newest for natural prompt ordering
    items.reverse()

    # Return compact history for prompt composition
    history = [
        {"user": it.get("user_query",""), "assistant": it.get("agent_response","")}
        for it in items if it.get("user_query") or it.get("agent_response")
    ]
    return {"history": history}
