# Orchestration Agent - Step Function Trigger
# Entry point that triggers the RAG pipeline orchestration to get the answers of user query/prompt

import json, os, uuid, time
import boto3
from datetime import datetime


sfn = boto3.client("stepfunctions")
STATE_MACHINE_ARN = os.environ.get("STEP_FUNCTION_RETRIEVAL_ARN", f"arn:aws:states:{os.environ.get('AWS_REGION', 'ap-south-1')}:{os.environ.get('AWS_ACCOUNT_ID')}:stateMachine:AaiKnowledgeRetrievalRagPipeline-{os.environ.get('ENVIRONMENT', 'dev')}")


def _extract_session_id(event_body, headers):
    # 1) body
    sid = (event_body or {}).get("session_id")
    if sid: return sid
    # 2) header
    if headers:
        sid = headers.get("X-Session-Id") or headers.get("x-session-id")
        if sid: return sid
        # 3) cookie
        cookie = headers.get("Cookie") or headers.get("cookie")
        if cookie:
            for part in cookie.split(";"):
                k, _, v = part.strip().partition("=")
                if k == "session_id" and v:
                    return v
    # 4) generate
    return str(uuid.uuid4())

def lambda_handler(event, context):
    start_time = time.time()
    
    try:
        headers = event.get("headers") or {}
        body_raw = event.get("body") or "{}"
        if isinstance(body_raw, str):
            body = json.loads(body_raw)
        else:
            body = body_raw

        user_query = body.get("user_query")
        if not user_query:
            return {"statusCode": 400, "body": json.dumps({"error":"user_query is required"})}

        # Generate unique identifiers
        session_id = _extract_session_id(body, headers)
        query_id = f"{session_id}_{int(time.time() * 1000)}_{str(uuid.uuid4())[:8]}"
        
        max_results = body.get("max_results", 5)
        product_filter = body.get("product_filter", None)
        use_reranker = body.get("use_reranker", False)
        use_mmr = body.get("use_mmr", False)
        mmr_lambda = body.get("mmr_lambda", 0.7)
        
        # Log request initiation
        request_log = {
            "event_type": "query_initiated",
            "timestamp": datetime.utcnow().isoformat(),
            "session_id": session_id,
            "query_id": query_id,
            "user_query": user_query,
            "parameters": {
                "max_results": max_results,
                "product_filter": product_filter,
                "use_reranker": use_reranker,
                "use_mmr": use_mmr
            },
            "source_ip": headers.get("X-Forwarded-For", "unknown"),
            "user_agent": headers.get("User-Agent", "unknown")
        }
        print(f"REQUEST_LOG: {json.dumps(request_log)}")

        sfn_input = {
            "session_id": session_id,
            "query_id": query_id,
            "user_query": user_query,
            "max_results": max_results,
            "product_filter": product_filter,
            "use_reranker": use_reranker,
            "use_mmr": use_mmr,
            "mmr_lambda": mmr_lambda
        }

        # Execute Step Function
        sfn_start = time.time()
        response = sfn.start_sync_execution(
            stateMachineArn=STATE_MACHINE_ARN,
            input=json.dumps(sfn_input)
        )
        sfn_duration = (time.time() - sfn_start) * 1000
        
        print("response", response)

        output_raw = response.get("output", "{}")
        if isinstance(output_raw, dict):
            output = output_raw
        else:
            output = json.loads(output_raw)

        print(f"Step Function Response: {output}")
        
        # Log Step Function execution
        execution_log = {
            "event_type": "step_function_completed",
            "timestamp": datetime.utcnow().isoformat(),
            "session_id": session_id,
            "query_id": query_id,
            "execution_arn": response.get("executionArn"),
            "status": response.get("status"),
            "duration_ms": sfn_duration,
            "billing_details": response.get("billingDetails", {})
        }
        print(f"EXECUTION_LOG: {json.dumps(execution_log)}")

        # Prepare response
        total_duration = (time.time() - start_time) * 1000
        
        response_body = {
            "query": user_query,
            "session_id": session_id,
            "query_id": query_id,
            "answer": output.get("answer", ""),
            "sources": output.get("sources", []),
            "monitoring": output.get("monitoring", {}),
            "timing": {
                "total_duration_ms": total_duration,
                "step_function_duration_ms": sfn_duration
            }
        }

        print(f"response_body: {response_body}")
        
        # Log successful response
        success_log = {
            "event_type": "query_completed",
            "timestamp": datetime.utcnow().isoformat(),
            "session_id": session_id,
            "query_id": query_id,
            "status": "success",
            "total_duration_ms": total_duration,
            "answer_length": len(output.get("answer", "")),
            "sources_count": len(output.get("sources", []))
        }
        print(f"SUCCESS_LOG: {json.dumps(success_log)}")
        
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Set-Cookie": f"session_id={session_id}; Path=/; HttpOnly; Secure; SameSite=Lax",
                "X-Query-Id": query_id,
                "X-Session-Id": session_id
            },
            "body": json.dumps(response_body)
        }
    except Exception as e:
        # Log error with session/query context
        error_log = {
            "event_type": "query_failed",
            "timestamp": datetime.utcnow().isoformat(),
            "session_id": locals().get("session_id", "unknown"),
            "query_id": locals().get("query_id", "unknown"),
            "error": str(e),
            "duration_ms": (time.time() - start_time) * 1000
        }
        print(f"ERROR_LOG: {json.dumps(error_log)}")
        
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            }, 
            "body": json.dumps({
                "error": str(e),
                "session_id": locals().get("session_id", "unknown"),
                "query_id": locals().get("query_id", "unknown")
            })
        }
