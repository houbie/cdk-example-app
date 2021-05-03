#!/usr/bin/env python3
import os

from aws_cdk import (
    core,
    aws_lambda as lambda_,
    aws_apigateway as apigw
)

PROJECT_DIR = os.path.dirname(__file__)


class CdkStack(core.Stack):

    def __init__(self, scope: core.Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        my_lambda = lambda_.Function(
            self, 'HelloHandler',
            function_name='hello-fn',
            runtime=lambda_.Runtime.PYTHON_3_8,
            code=self.asset('cdk_example_app/hello'),
            handler='hello.handler',
        )

        apigw.LambdaRestApi(
            self, 'CdkExampleApi',
            handler=my_lambda,
        )

    @staticmethod
    def asset(relative_path):
        """Turn a path relative to the project dir into a lambda code asset.
        This makes it possible to test stack creation from within the test dir"""
        return lambda_.Code.from_asset(os.path.join(PROJECT_DIR, relative_path))


app = core.App()
CdkStack(app, "cdk-example-app", env={'region': 'eu-west-1'})

app.synth()
