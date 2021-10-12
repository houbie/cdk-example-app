import os


def hello_world():
    return {"greeting": "Hello world!!", "region": os.environ["AWS_REGION"]}
