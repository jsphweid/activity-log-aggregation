import os

GITHUB_ACCESS_TOKEN = os.environ.get('GITHUB_ACCESS_TOKEN', None)
GITHUB_USER = os.environ.get('GITHUB_USER', None)
NOTION_EMAIL = os.environ.get('NOTION_EMAIL', None)
NOTION_TOKEN_V2 = os.environ.get('NOTION_TOKEN_V2', None)
NOTION_SPACE_ID = os.environ.get('NOTION_SPACE_ID', None)
DYNAMODB_CLIENT_CONFIG = {} if os.environ.get('LOCAL_DB', 'false') != 'true' else {
    'region_name': 'localhost',
    'endpoint_url': 'http://localhost:8000',
    'aws_access_key_id': 'access_key_id',
    'aws_secret_access_key': 'secret_access_key'
}
DYNAMODB_TABLE_NAME = os.environ['DYNAMODB_TABLE_NAME']
