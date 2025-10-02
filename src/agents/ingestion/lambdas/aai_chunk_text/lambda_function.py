import json
import os
import boto3

s3 = boto3.client('s3')
CHUNK_BATCH_SIZE = int(os.environ.get("CHUNK_BATCH_SIZE", "20"))

def batch_chunks(chunk_keys, batch_size=CHUNK_BATCH_SIZE):
    return [chunk_keys[i:i + batch_size] for i in range(0, len(chunk_keys), batch_size)]

def lambda_handler(event, context):
    try:
        bucket = event["bucket"]
        json_key = event["jsonKey"]
        layout_textract_json = s3.get_object(Bucket=bucket, Key=json_key)["Body"].read().decode("utf-8")
        textract_data = json.loads(layout_textract_json)

        chunks = []
        current_chunk = ""

        # Get layout blocks and their child text
        for block in textract_data.get('Blocks', []):
            if block.get('BlockType') in ['LAYOUT_SECTION_HEADER', 'LAYOUT_TEXT', 'LAYOUT_LIST', 'LAYOUT_TABLE']:
                # Get text from child LINE blocks
                text_content = ""
                if 'Relationships' in block:
                    for rel in block['Relationships']:
                        if rel['Type'] == 'CHILD':
                            for child_id in rel['Ids']:
                                # Find child block
                                for child_block in textract_data.get('Blocks', []):
                                    if child_block['Id'] == child_id and child_block.get('BlockType') == 'LINE':
                                        text_content += child_block.get('Text', '') + "\n"
                
                if text_content.strip():
                    layout_type = block.get('BlockType', '')
                    
                    if layout_type in ['LAYOUT_SECTION_HEADER']:
                        # Start new chunk with header
                        if current_chunk.strip():
                            chunks.append(current_chunk.strip())
                        current_chunk = text_content
                    elif layout_type in ['LAYOUT_TEXT', 'LAYOUT_LIST', 'LAYOUT_TABLE']:
                        # Add to current chunk
                        current_chunk += text_content

        if current_chunk.strip():
            chunks.append(current_chunk.strip())

        print(f"Chunking completed. Generated {len(chunks)} chunks")

        chunk_objects = []
        for idx, chunk in enumerate(chunks):
            chunk_data = {"source": json_key, "chunk_id": idx, "text": chunk}
            chunk_key = json_key.replace("processed/json/", "processed/chunks/") + f"_{idx}.json"
            s3.put_object(Body=json.dumps(chunk_data), Bucket=bucket, Key=chunk_key)
            chunk_objects.append(chunk_key)

        chunk_batches = batch_chunks(chunk_objects)
        return {"statusCode": 200, "chunkBatches": chunk_batches, "bucket": bucket}
        
    except Exception as e:
        import traceback
        error_msg = f"Error: {str(e)}\nTraceback: {traceback.format_exc()}"
        print(error_msg)
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }