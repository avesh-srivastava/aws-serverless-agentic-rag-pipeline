# Conversation Agent - Answer Synthesizer
# Generates responses using Bedrock LLM with retrieved context

import os, json, boto3, textwrap
bedrock = boto3.client("bedrock-runtime")
LLM_MODEL = os.environ.get("LLM_MODEL", "amazon.titan-text-lite-v1")

# Prompt template (keep concise)
PROMPT_TEMPLATE = """
You are a customer support assistant. You MUST ONLY use the short chat history and the knowledge context to answer.

IMPORTANT RULES:
1. ONLY answer using information from the knowledge context below
2. If the answer is NOT in the context, respond EXACTLY: "I don't know — would you like me to raise a ticket for our support team?"
3. Do NOT use your general knowledge or training data
4. Do NOT say things like "I don't have access to current information"

Chat history (most recent last):
{chat_history}

Knowledge context:
{context}

User question: {question}

Answer concisely and use ONLY the Chat history and knowledge context above . If possible, include short citations like [ticket_id/doc_id] you used at the end as "Sources: [id1, id2].
"""

def format_history(history):
    # history: [{"user": "...", "assistant": "..."}, ...]
    lines = []
    for turn in history or []:
        u = turn.get("user_query")
        a = turn.get("agent_response")
        if u: lines.append(f"User: {u}")
        if a: lines.append(f"Assistant: {a}")
    return "\n".join(lines)



def lambda_handler(event, context):
    user_query = event.get("user_query")
    chunks = event.get("chunks", [])[:10]
    metadata = event.get("metadata", [])
    history = event.get("conversationHistory", [])

    chat_history = format_history(history) or "(No previous conversation)"
    # Prepare context: concatenate top chunks with small separators and limit total size
    context_text = "\n\n---\n\n".join(chunks)
    # Optionally truncate to keep prompt under token limit (simple char-based truncation)
    max_chars = int(os.environ.get("PROMPT_MAX_CHARS", "3500"))
    if len(context_text) > max_chars:
        context_text = context_text[-max_chars:]  # keep last part

    prompt = PROMPT_TEMPLATE.format(
        chat_history=chat_history,
        context=context_text,
        question=user_query
    )

    payload = json.dumps({
        "inputText": prompt,
        # additional model-specific params can go here
    })


    print(f"payload: {payload}")


    resp = bedrock.invoke_model(modelId=LLM_MODEL, body=payload)
    body = resp['body'].read()
    result = json.loads(body)
    answer = result.get("outputText") or result.get("content") or str(result)

    # Collect top source ids to return as citation
    source_ids = [m.get("ticket_id") or m.get("source") for m in metadata if m.get("ticket_id") or m.get("source")]
    source_ids = list(dict.fromkeys(source_ids))  # dedupe preserving order

    # Check if user wants to create a ticket
    user_query_lower = user_query.lower()
    wants_ticket = any(phrase in user_query_lower for phrase in [
        'yes', 'create ticket', 'raise ticket', 'support ticket', 
        'contact support', 'escalate', 'help me'
    ])
    
    return {
        "answer": answer.strip(), 
        "sources": source_ids,
        "create_ticket": wants_ticket
    }
