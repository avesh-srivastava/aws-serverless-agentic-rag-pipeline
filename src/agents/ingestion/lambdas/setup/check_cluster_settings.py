import boto3
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth
import os

def check_settings():
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
    
    # Check cluster settings
    settings = opensearch.cluster.get_settings()
    print("Cluster settings:", settings)
    
    # Check if k-NN plugin is installed
    plugins = opensearch.cat.plugins(format='json')
    print("Installed plugins:", plugins)

if __name__ == "__main__":
    check_settings()