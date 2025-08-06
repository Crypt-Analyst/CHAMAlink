import boto3
import os
import json

def get_secret(secret_name, region_name=None):
    region = region_name or os.getenv('AWS_REGION', 'us-east-1')
    client = boto3.client('secretsmanager', region_name=region)
    response = client.get_secret_value(SecretId=secret_name)
    secret = response.get('SecretString')
    if secret:
        return json.loads(secret)
    return None
