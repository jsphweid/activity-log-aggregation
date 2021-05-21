import os

SIMPLE_TABLE_NAME = "ActivityLogAggregationTable"


def setup_local_env(local_db=True):
    with open('prod.env', 'r') as reader:
        contents = reader.read()
    for item in contents.split('\n'):
        key, value = item.split('=')
        os.environ[key] = value

    if local_db:
        os.environ["LOCAL_DB"] = "true"
        os.environ["DYNAMODB_TABLE_NAME"] = SIMPLE_TABLE_NAME
    else:
        import boto3
        client = boto3.client('dynamodb', region_name=os.environ.get("AWS_DEFAULT_REGION", "us-west-2"))

        # TODO: above 100 table search would have to be implemented
        response = client.list_tables(Limit=100)
        real_table_name = next(name for name in response["TableNames"] if SIMPLE_TABLE_NAME in name)
        os.environ["DYNAMODB_TABLE_NAME"] = real_table_name
