#!/usr/bin/env python3
import os
import random

from aws_cdk import (
    core,
    aws_apigateway,
    aws_s3,
)

from cdk_lib.api_gw import RestApi
from cdk_lib.event_log import event_log_table
from cdk_lib.lambda_function import lambda_function, s3_event_handler
from cdk_lib.stack import PythonStack

PROJECT_DIR = os.path.dirname(__file__)


def get_bucket_name():
    return f'{os.getenv("USER", default=str(random.randint(0, 1000)).lower())}-cdk-example-app-events'


S3_EVENT_PATH = 's3-integration-event'


class ApplicationStack(PythonStack):

    def __init__(self, scope: core.Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        event_log = event_log_table(self)

        api_lambda = lambda_function(self, 'Api')

        events_bucket = aws_s3.Bucket(self, "EventsBucket", bucket_name=get_bucket_name())
        s3_event_handler(self, 'S3IntegrationEvent', events_bucket,
                         s3_key_prefix=S3_EVENT_PATH, event_log_table=event_log)

        apigw = RestApi(self, 'CdkExampleApi')
        apigw.root.add_proxy(default_integration=aws_apigateway.LambdaIntegration(api_lambda))
        apigw.add_s3_integration(S3_EVENT_PATH, bucket=events_bucket)


class SupportStack(PythonStack):
    pass


app = core.App()
ApplicationStack(app, 'CdkExampleApp', env={'region': 'eu-west-1'})
SupportStack(app, 'CdkExampleAppSupport', env={'region': 'eu-west-1'})

app.synth()
