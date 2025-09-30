from sagemaker.huggingface.model import HuggingFacePredictor
import boto3
import sagemaker
import os

# 1. Configure region and session
region = os.environ.get("AWS_REGION")

session = boto3.Session(region_name=region)
sagemaker_session = sagemaker.Session(boto_session=session)

#replace your model name here 
predictor = HuggingFacePredictor("minilm-reranker-1756624753", sagemaker_session=sagemaker_session)

query = "What is the capital of France?"
docs = [
    "Paris is the capital city of France.",
    "Berlin is the capital of Germany."
]

# Test each document pair individually
for i, doc in enumerate(docs):
    pair = {"inputs": [query, doc]}
    response = predictor.predict(pair)
    print(f"Doc {i+1} score:", response)
