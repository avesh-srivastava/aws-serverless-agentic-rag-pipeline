import boto3
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth
import os

def enable_knn():
    host = os.environ.get("OPENSEARCH_DOMAIN")
    region = os.environ.get("AWS_REGION")
    service = 'es'
    
    credentials = boto3.Session().get_credentials()
    awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, 
                       region, service, session_token=credentials.token)
    
    opensearch = OpenSearch(
        hosts = [{'host': host, 'port': 443}],
        http_auth = awsauth,
        use_ssl = True,
        verify_certs = True,
        connection_class = RequestsHttpConnection
    )
    
    # Enable k-NN plugin
    settings = {
        "persistent": {
            "knn.plugin.enabled": True,
            "knn.algo_param.index_thread_qty": 2
        }
    }
    
    response = opensearch.cluster.put_settings(body=settings)
    print("k-NN plugin enabled:", response)

if __name__ == "__main__":
    enable_knn()