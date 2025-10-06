#!/usr/bin/env python3
"""
Update Lambda Environment Variables
This script updates existing Lambda functions with proper environment variables.
Needed for maintenance - When Terraform state is lost or functions deployed outside Terraform
Operational tool - Useful for fixing environment variable issues
"""

import boto3
import json
import sys
from typing import Dict

def get_terraform_outputs() -> Dict:
    """Get Terraform outputs for environment variables."""
    try:
        with open('../configs/terraform-outputs-dev.json', 'r') as f:
            outputs = json.load(f)
        return outputs['environment_config']['value']
    except Exception as e:
        print(f"Error reading Terraform outputs: {e}")
        sys.exit(1)

def update_lambda_env_vars(function_name: str, env_vars: Dict) -> bool:
    """Update environment variables for a Lambda function."""
    lambda_client = boto3.client('lambda')
    
    try:
        # Get current function configuration
        response = lambda_client.get_function(FunctionName=function_name)
        current_env = response['Configuration'].get('Environment', {}).get('Variables', {})
        
        # Merge with new environment variables
        updated_env = {**current_env, **env_vars}
        
        # Update function configuration
        lambda_client.update_function_configuration(
            FunctionName=function_name,
            Environment={'Variables': updated_env}
        )
        
        print(f"[SUCCESS] Updated {function_name} with {len(env_vars)} environment variables")
        return True
        
    except Exception as e:
        print(f"[ERROR] Failed to update {function_name}: {e}")
        return False

def main():
    """Main function to update all Lambda environment variables."""
    print("Updating Lambda function environment variables...")
    
    # Get Terraform outputs
    config = get_terraform_outputs()
    
    # Common environment variables
    common_env_vars = {
        'ENVIRONMENT': config['environment'],
        'OPENSEARCH_DOMAIN': config['opensearch_domain'],
        'OPENSEARCH_INDEX': config['opensearch_index'],
        'CONVERSATION_TABLE': config['conversation_table'],
        'SUPPORT_TICKETS_TABLE': config['support_tickets_table'],
        'RAW_DATA_BUCKET': config['raw_data_bucket'],
        'SEARCH_RESULTS_BUCKET': config['search_results_bucket'],
        'LLM_MODEL': config['llm_model'],
        'EMBED_MODEL': config['embed_model'],
        'HF_MODEL_ID': config['hf_model_id'],
        'HF_TASK': config['hf_task'],
        'SUPPORT_EMAIL': config['support_email'],
        'TTL_DAYS': str(config['ttl_days'])
    }
    
    # Agent-specific configurations
    agent_configs = config['agent_configs']
    
    # Function to agent mapping
    function_agent_map = {
        'aai_start_textract': 'ingestion',
        'aai_check_textract_status': 'ingestion',
        'aai_preprocess_csv': 'ingestion',
        'aai_chunk_text': 'ingestion',
        'aai_generate_embeddings': 'ingestion',
        'aai_create_opensearch_index': 'ingestion',
        'aai_store_opensearch': 'ingestion',
        'aai_hybrid_search_fusion': 'retrieval',
        'aai_cross_encoder_rerank': 'retrieval',
        'aai_mmr_diversity': 'retrieval',
        'aai_final_results': 'retrieval',
        'aai_query_embedding': 'conversation',
        'aai_read_history': 'conversation',
        'aai_synthesize_answer': 'conversation',
        'aai_store_conversation': 'conversation',
        'aai_create_ticket': 'escalation',
        'aai_trigger_step_function_ingestion': 'orchestration',
        'aai_trigger_step_function_retrieval': 'orchestration'
    }
    
    # Get existing Lambda functions
    lambda_client = boto3.client('lambda')
    response = lambda_client.list_functions()
    existing_functions = [f['FunctionName'] for f in response['Functions'] if f['FunctionName'].startswith('aai_')]
    
    success_count = 0
    total_count = 0
    
    for function_name in existing_functions:
        if function_name in function_agent_map:
            agent = function_agent_map[function_name]
            
            # Prepare environment variables for this function
            function_env_vars = {
                **common_env_vars,
                'AGENT_NAME': agent,
                'LAMBDA_FUNCTION_NAME': function_name,
                **agent_configs[agent]['environment_vars']
            }
            
            total_count += 1
            if update_lambda_env_vars(function_name, function_env_vars):
                success_count += 1
        else:
            print(f"[WARNING] Unknown function: {function_name}")
    
    print(f"\nSummary: {success_count}/{total_count} functions updated successfully")
    
    if success_count == total_count:
        print("[SUCCESS] All Lambda functions updated with proper environment variables!")
        sys.exit(0)
    else:
        print("[ERROR] Some functions failed to update")
        sys.exit(1)

if __name__ == "__main__":
    main()