import os
import json
import re
import csv
import boto3
from datetime import datetime

s3 = boto3.client("s3")

# Configuration via env vars
OUTPUT_PREFIX = os.environ.get("OUTPUT_PREFIX", "processed/chunks/logs/")
CHUNK_CHAR_SIZE = int(os.environ.get("CHUNK_CHAR_SIZE", "1200"))
CHUNK_OVERLAP = int(os.environ.get("CHUNK_OVERLAP", "200"))
CHUNK_BATCH_SIZE = int(os.environ.get("CHUNK_BATCH_SIZE", "20"))


# Basic PII regexes (extend as needed)
EMAIL_RE = re.compile(r'[\w\.-]+@[\w\.-]+\.\w+')
PHONE_RE = re.compile(r'(\+?\d[\d\-\s]{7,}\d)')
CREDIT_CARD_RE = re.compile(r'\b(?:\d[ -]*?){13,19}\b')  # rough credit-card-like numbers
SSN_RE = re.compile(r'\b\d{3}-\d{2}-\d{4}\b')  # US SSN format

def redact_pii(text: str) -> str:
    if not text:
        return text
    # Replace emails
    text = EMAIL_RE.sub("[REDACTED_EMAIL]", text)
    # Replace phone-like numbers
    text = PHONE_RE.sub("[REDACTED_PHONE]", text)
    # Replace credit-card-like sequences
    text = CREDIT_CARD_RE.sub("[REDACTED_NUMBER]", text)
    # Replace SSN-like patterns
    text = SSN_RE.sub("[REDACTED_SSN]", text)
    return text

def normalize_whitespace(text: str) -> str:
    return re.sub(r'\s+', ' ', text).strip()

def build_ticket_text(record: dict) -> str:
    """
    Build a combined text blob for embedding from only the specified fields:
    Product Purchased, Ticket Subject, Ticket Description, Resolution
    """
    parts = []
    if record.get("product_purchased"):
        parts.append(record.get('product_purchased'))
    if record.get("subject"):
        parts.append(record.get('subject'))
    if record.get("description"):
        parts.append(record.get('description'))
    if record.get("resolution"):
        parts.append(record.get('resolution'))
    combined = " ".join(parts)
    combined = normalize_whitespace(combined)
    combined = redact_pii(combined)
    return combined

def chunk_text_with_overlap(text: str, chunk_size=CHUNK_CHAR_SIZE, overlap=CHUNK_OVERLAP):
    """
    Create overlapping chunks of the text.
    Returns list of strings.
    """
    if not text:
        return []
    text_len = len(text)
    chunks = []
    start = 0
    while start < text_len:
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        if end >= text_len:
            break
        start = end - overlap  # slide with overlap
    return chunks

def read_s3_object(bucket, key) -> str:
    resp = s3.get_object(Bucket=bucket, Key=key)
    body = resp['Body'].read()
    return body.decode('utf-8')

def write_json_s3(obj: dict, bucket: str, key: str):
    s3.put_object(Bucket=bucket, Key=key, Body=json.dumps(obj).encode('utf-8'))

def batch_chunks(chunk_keys, batch_size=CHUNK_BATCH_SIZE):
    return [chunk_keys[i:i + batch_size] for i in range(0, len(chunk_keys), batch_size)]

def process_csv_file(bucket: str, key: str):
    """
    Reads CSV from S3, expects header row with at least these columns:
    ticket_id, product_purchased, type, subject, description, status, resolution, priority, channel
    """
    # Extract filename without extension
    filename = os.path.splitext(os.path.basename(key))[0]
    
    raw = read_s3_object(bucket, key)
    # Use csv.DictReader to parse
    lines = raw.splitlines()
    reader = csv.DictReader(lines)
    created_keys = []
    for row in reader:
        # Normalize keys: strip whitespace from headers/values
        record = {k.strip(): (v.strip() if isinstance(v, str) else v) for k, v in row.items()}
        # Expected keys lowercased mapping
        # allow case-insensitive header names
        normalized = {
            "ticket_id": record.get("ticket_id"),
            "product_purchased": record.get("product_purchased"),
            "type": record.get("type"),
            "subject": record.get("subject"),
            "description": record.get("description"),
            "status": record.get("status"),
            "resolution": record.get("resolution"),
            "priority": record.get("priority"),
            "channel": record.get("channel")
        }

        ticket_id = str(normalized.get("ticket_id") or f"noid_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}")
        combined_text = build_ticket_text(normalized)
        # Chunk
        chunks = chunk_text_with_overlap(combined_text)
        # Save each chunk as JSON to S3
        for idx, chunk_text in enumerate(chunks):
            chunk_obj = {
                "source": "support_log",
                "ticket_id": ticket_id,
                "chunk_id": idx,
                "text": chunk_text,  # Only embedding fields: Product Purchased, Subject, Description, Resolution
                "metadata": {
                    "product_purchased": normalized.get("product_purchased"), # required in metadata as well for filteration
                    "type": normalized.get("type"),
                    "priority": normalized.get("priority"),
                    "channel": normalized.get("channel"),
                    "status": normalized.get("status")
                },
                "created_at": datetime.utcnow().isoformat()
            }
            # safe key name
            safe_ticket = re.sub(r'[^a-zA-Z0-9_\-]', '_', ticket_id)
            safe_filename = re.sub(r'[^a-zA-Z0-9_\-]', '_', filename)
            out_key = f"{OUTPUT_PREFIX}{safe_filename}_ticket_{safe_ticket}_chunk_{idx}.json"
            write_json_s3(chunk_obj, bucket, out_key)
            created_keys.append(out_key)

    chunk_batches = batch_chunks(created_keys)
    return chunk_batches

def lambda_handler(event, context):
    """
    Lambda entrypoint. Expect either:
    - event with 'bucket' and 'key' (invoked from Step Functions), or
    - standard S3 put event (Records)
    """
    # Extract bucket/key
    print(f"event: {event}")
    if "bucket" in event and "key" in event:
        bucket = event["bucket"]
        key = event["key"]
    else:
        raise ValueError("Missing bucket or key in event")

    print(f"Processing CSV s3://{bucket}/{key}")
    batches = process_csv_file(bucket, key)
    print(f"Created {len(batches)} chunk batches")
    return {"status": "ok", "chunkBatches": batches, "bucket": bucket}
