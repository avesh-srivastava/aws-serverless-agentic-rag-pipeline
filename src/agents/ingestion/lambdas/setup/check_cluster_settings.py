import boto3
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth

def check_settings():
    host = 'search-customer-support-search-w3mis3dcb66vl4ojauchjsffj4.us-east-1.es.amazonaws.com'
    region = 'us-east-1'
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