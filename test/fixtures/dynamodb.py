import os
import tarfile

import pytest
import requests
from cdk_example_app.common.event_log import EventLog
from pytest_dynamodb import factories


def download_dynamodb_local(target_dir):
    url = 'https://s3-us-west-2.amazonaws.com/dynamodb-local/dynamodb_local_latest.tar.gz'
    local_filename = url.split('/')[-1]
    with requests.get(url, stream=True) as r:
        with open(local_filename, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
    with tarfile.open(local_filename, 'r:gz') as tar:
        tar.extractall(path=target_dir)
    os.remove(local_filename)
    print(f'downloaded local dynamodb to {target_dir}')


dynamo_dir = os.path.join(os.path.dirname(__file__), "../../.dynamodb")
if not os.path.exists(f"{dynamo_dir}/DynamoDBLocal.jar"):
    download_dynamodb_local(dynamo_dir)

dynamodb_proc = factories.dynamodb_proc(dynamo_dir)


@pytest.fixture
def event_log_table(dynamodb):
    EventLog.Meta.host = dynamodb.meta.client.meta.endpoint_url
    EventLog.create_table(read_capacity_units=1, write_capacity_units=1, wait=True)
    yield dynamodb
    EventLog.delete_table()  # TODO: this should not be necessary
