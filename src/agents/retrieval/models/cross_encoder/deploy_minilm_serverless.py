from sagemaker.huggingface import HuggingFaceModel
from sagemaker.serverless import ServerlessInferenceConfig
import sagemaker
import boto3
import time
import os

# 1. Configure region and session
region = os.environ.get("AWS_REGION")

session = boto3.Session(region_name=region)
sagemaker_session = sagemaker.Session(boto_session=session)

# 2. Get execution role
aws_account_id = os.environ.get('AWS_ACCOUNT_ID')
if not aws_account_id:
    raise ValueError("AWS_ACCOUNT_ID environment variable is required")
role = f"arn:aws:iam::{aws_account_id}:role/CsSageMakerExecutionRole"

#role = os.environ.get('SAGEMAKER_ROLE_ARN', f"arn:aws:iam::{os.environ.get('AWS_ACCOUNT_ID')}:role/AgenticRag-SageMaker-Role-{os.environ.get('ENVIRONMENT', 'dev')}")

# 3. Model config
HF_MODEL_ID = os.environ.get("HF_MODEL_ID")
HF_TASK = os.environ.get("HF_TASK")

hub = {
    'HF_MODEL_ID': HF_MODEL_ID,
    'HF_TASK': HF_TASK
}

# 4. Create HuggingFace model object
huggingface_model = HuggingFaceModel(
    env=hub,
    role=role,
    transformers_version="4.37",
    pytorch_version="2.1",
    py_version="py310",
    sagemaker_session=sagemaker_session
)

# 5. Serverless config (Pay-Per-Use)
serverless_config = ServerlessInferenceConfig(
    memory_size_in_mb=3072,   # 3GB
    max_concurrency=5,
)

# 6. Deploy endpoint
endpoint_name = f"minilm-reranker-{int(time.time())}"
predictor = huggingface_model.deploy(
    endpoint_name=endpoint_name,
    serverless_inference_config=serverless_config
)

print(f"Endpoint name: {endpoint_name}")

print("Deployed endpoint:", predictor.endpoint_name)
