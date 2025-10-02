# Data Ingestion Agent - Textract Status Checker
# Monitors Textract job completion status

import boto3
import json

s3 = boto3.client('s3')
textract = boto3.client('textract')

def lambda_handler(event, context):
    job_id  = event["Payload"]["jobId"]
    bucket  = event["Payload"]["bucket"]
    key     = event["Payload"]["key"]
   
    print("JobId: " + job_id, "Bucket: " + bucket, "Key: " + key)

    #result = textract.get_document_text_detection(JobId=job_id)
    result = textract.get_document_analysis(JobId=job_id)

    status = result["JobStatus"]

    print("Textract API call completed")
    print("result:", result)

    if status == "SUCCEEDED":
        # text = " ".join([item["Text"] for item in result["Blocks"] if item["BlockType"] == "LINE"])
        # out_key = key.replace("raw/", "processed/text/") + ".txt"
        # s3.put_object(Body=text.encode('utf-8'), Bucket=bucket, Key=out_key)

        out_key = key.replace("raw/", "processed/json/") + ".json"
        s3.put_object(Body=json.dumps(result).encode('utf-8'), Bucket=bucket, Key=out_key)
        return {"textractStatus": "SUCCEEDED", "textKey": out_key, "bucket": bucket}
        
    else:
        return {"textractStatus": status, "jobId": job_id, "bucket": bucket, "key": key}
