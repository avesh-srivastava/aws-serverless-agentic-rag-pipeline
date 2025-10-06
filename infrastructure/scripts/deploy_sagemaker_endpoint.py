#!/usr/bin/env python3
"""
Deploy SageMaker Cross-Encoder Endpoint
Uses the existing deployment script with proper environment setup.
"""

import os
import sys
import subprocess
import boto3

def deploy_sagemaker_endpoint():
    """Deploy the SageMaker cross-encoder endpoint."""
    
    print("Deploying SageMaker Cross-Encoder Endpoint...")
    
    # Set environment variables
    env = os.environ.copy()
    env.update({
        'AWS_REGION': 'ap-south-1',
        'AWS_ACCOUNT_ID': '286519251843',
        'HF_MODEL_ID': 'cross-encoder/ms-marco-MiniLM-L-6-v2',
        'HF_TASK': 'text-classification'
    })
    
    # Path to the existing deployment script
    script_path = os.path.join(
        os.path.dirname(__file__),
        '../../src/agents/retrieval/models/cross_encoder/deploy_minilm_serverless.py'
    )
    
    try:
        # Run the deployment script
        result = subprocess.run(
            [sys.executable, script_path],
            env=env,
            capture_output=True,
            text=True,
            cwd=os.path.dirname(script_path)
        )
        
        if result.returncode == 0:
            print("[SUCCESS] SageMaker endpoint deployed successfully!")
            print(result.stdout)
            
            # Extract endpoint name from output
            lines = result.stdout.split('\n')
            endpoint_name = None
            for line in lines:
                if 'Endpoint name:' in line:
                    endpoint_name = line.split(':')[1].strip()
                    break
                elif 'Deployed endpoint:' in line:
                    endpoint_name = line.split(':')[1].strip()
                    break
            
            if endpoint_name:
                print(f"Updating Lambda environment variables with endpoint: {endpoint_name}")
                update_lambda_env_vars(endpoint_name)
            
            return endpoint_name
            
        else:
            print("[ERROR] Failed to deploy SageMaker endpoint:")
            print(result.stderr)
            sys.exit(1)
            
    except Exception as e:
        print(f"[ERROR] Error running deployment script: {e}")
        sys.exit(1)

def update_lambda_env_vars(endpoint_name):
    """Update Lambda functions with SageMaker endpoint name."""
    lambda_client = boto3.client('lambda', region_name='ap-south-1')
    
    # Functions that need the endpoint
    functions_to_update = ['aai_cross_encoder_rerank']
    
    for function_name in functions_to_update:
        try:
            response = lambda_client.get_function(FunctionName=function_name)
            current_env = response['Configuration'].get('Environment', {}).get('Variables', {})
            
            # Add endpoint name
            updated_env = {**current_env, 'SAGEMAKER_ENDPOINT': endpoint_name}
            
            lambda_client.update_function_configuration(
                FunctionName=function_name,
                Environment={'Variables': updated_env}
            )
            
            print(f"[SUCCESS] Updated {function_name} with endpoint: {endpoint_name}")
            
        except Exception as e:
            print(f"[WARNING] Failed to update {function_name}: {e}")

if __name__ == "__main__":
    endpoint_name = deploy_sagemaker_endpoint()
    if endpoint_name:
        print(f"\nDeployment complete! Endpoint: {endpoint_name}")
    else:
        print("[ERROR] Deployment failed - no endpoint name found")
        sys.exit(1)