import os
import tarfile

import pytest
import requests
from pytest_dynamodb import factories

from cdk_example_app.common.event_log import EventLog

os.environ["AWS_REGION"] = "eu-west-1"


def download_dynamodb_local(target_dir):
    url = "https://s3-us-west-2.amazonaws.com/dynamodb-local/dynamodb_local_latest.tar.gz"
    local_filename = url.split("/", maxsplit=1)[0]
    with requests.get(url, stream=True) as resp:
        with open(local_filename, "wb") as file:
            for chunk in resp.iter_content(chunk_size=8192):
                file.write(chunk)
    with tarfile.open(local_filename, "r:gz") as tar:
        def is_within_directory(directory, target):
            
            abs_directory = os.path.abspath(directory)
            abs_target = os.path.abspath(target)
        
            prefix = os.path.commonprefix([abs_directory, abs_target])
            
            return prefix == abs_directory
        
        def safe_extract(tar, path=".", members=None, *, numeric_owner=False):
        
            for member in tar.getmembers():
                member_path = os.path.join(path, member.name)
                if not is_within_directory(path, member_path):
                    raise Exception("Attempted Path Traversal in Tar File")
        
            tar.extractall(path, members, numeric_owner=numeric_owner) 
            
        
        safe_extract(tar, path=target_dir)
    os.remove(local_filename)
    print(f"downloaded local dynamodb to {target_dir}")


dynamo_dir = os.path.join(os.path.dirname(__file__), "../../.dynamodb")
if not os.path.exists(f"{dynamo_dir}/DynamoDBLocal.jar"):
    download_dynamodb_local(dynamo_dir)

dynamodb_proc = factories.dynamodb_proc(dynamo_dir)


@pytest.fixture
def event_log_table(dynamodb):
    EventLog.Meta.host = dynamodb.meta.client.meta.endpoint_url
    EventLog.create_table(read_capacity_units=1, write_capacity_units=1, wait=True)
    yield dynamodb
    EventLog.delete_table()
