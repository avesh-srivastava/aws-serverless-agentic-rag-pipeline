from sagemaker.huggingface.model import HuggingFacePredictor
import boto3
import sagemaker

# 1. Configure region and session
session = boto3.Session(region_name='us-east-1')
sagemaker_session = sagemaker.Session(boto_session=session)

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
