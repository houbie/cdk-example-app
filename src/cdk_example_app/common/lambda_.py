from functools import lru_cache

import boto3


@lru_cache
def lambda_client():
    return boto3.client('lambda')


def get_function_info(lambda_arn):
    fn_info = lambda_client().get_function(FunctionName=lambda_arn)
    info = {'lastModified': fn_info['Configuration']['LastModified']}
    info.update(lambda_client().list_tags(Resource=lambda_arn)['Tags'])
    return info
