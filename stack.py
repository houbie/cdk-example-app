#!/usr/bin/env python3
import os
import random
import subprocess
from hashlib import sha256
from pathlib import Path

from aws_cdk import (
    core,
    aws_lambda,
    aws_apigateway,
    aws_s3,
    aws_iam
)

PROJECT_DIR = os.path.dirname(__file__)
STACK_NAME = 'cdk-example-app'


class CdkStack(core.Stack):

    def __init__(self, scope: core.Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        dependencies_layer = self.create_dependencies_layer()

        hello_lambda = aws_lambda.Function(
            self, 'HelloHandler',
            function_name='hello-fn',
            runtime=aws_lambda.Runtime.PYTHON_3_8,
            code=self.asset('cdk_example_app'),
            handler='hello/hello.handler',
            layers=[
                dependencies_layer
            ]
        )

        events_bucket_name = f'{os.getenv("USER", default=str(random.randint(0, 1000)).lower())}-cdk-example-app-events'
        events_bucket = aws_s3.Bucket(self, "EventsBucket", bucket_name=events_bucket_name)
        events_bucket_apigw_role = aws_iam.Role(self, "EventsBucketApigwRole",
                                                assumed_by=aws_iam.ServicePrincipal(
                                                    'apigateway.amazonaws.com').grant_principal)
        events_bucket.grant_read_write(events_bucket_apigw_role)

        apigw = aws_apigateway.LambdaRestApi(self, 'CdkExampleApi', handler=hello_lambda, proxy=False)
        apigw.root.add_resource('hello').add_resource('{proxy+}').add_method(
            'GET', aws_apigateway.LambdaIntegration(hello_lambda))

        self.add_s3_integration(apigw, path='s3-integration-event', bucket=events_bucket,
                                s3_key_prefix='s3-integration-event', role=events_bucket_apigw_role)

    @staticmethod
    def asset(relative_path):
        """Turn a path relative to the project dir into a lambda code asset.
        This makes it possible to test stack creation from within the test dir"""
        return aws_lambda.Code.from_asset(os.path.join(PROJECT_DIR, relative_path))

    def create_dependencies_layer(self) -> aws_lambda.LayerVersion:
        layers_dir = Path(PROJECT_DIR, '.layers')
        layers_dir.mkdir(exist_ok=True)
        requirements = subprocess.check_output(
            f'poetry export --with-credentials --without-hashes'.split()
        ).decode("utf-8")
        requirements = '\n'.join([line for line in requirements.splitlines() if not line.startswith('boto')])

        requirements_hash = sha256(requirements.encode('utf-8')).hexdigest()
        destination_dir = layers_dir.joinpath(requirements_hash)
        if not destination_dir.exists():
            destination_dir.mkdir()
            requirements_file = destination_dir.joinpath('requirements.txt')
            with requirements_file.open('w') as f:
                f.write(requirements)
            print('running pip install...')
            subprocess.check_call(f'pip install --no-deps -r {requirements_file} -t {destination_dir}/python'.split())

        layer_id = f'{STACK_NAME}-dependencies'
        layer_code = aws_lambda.Code.from_asset(str(destination_dir))

        return aws_lambda.LayerVersion(self, layer_id, code=layer_code)

    @staticmethod
    def add_s3_integration(apigw, path, bucket, s3_key_prefix, role):
        integration_options = aws_apigateway.IntegrationOptions(
            credentials_role=role,
            integration_responses=[aws_apigateway.IntegrationResponse(
                status_code='202',
                selection_pattern='2\\d{2}',
                response_templates={'application/json': '{"requestId": "$context.requestId"}'}
            )],
            passthrough_behavior=aws_apigateway.PassthroughBehavior.WHEN_NO_MATCH,
            request_parameters={
                'integration.request.header.Content-Type': 'method.request.header.Content-Type',
                # we can save headers as as meta data on the S3 object
                'integration.request.header.x-amz-meta-b3': 'method.request.header.b3',
                'integration.request.header.x-amz-meta-x-b3-traceid': 'method.request.header.x-b3-traceid',
                'integration.request.header.x-amz-meta-x-b3-spanid': 'method.request.header.x-b3-spanid',
                'integration.request.header.x-amz-meta-x-b3-sampled': 'method.request.header.x-b3-sampled',
                'integration.request.header.x-amz-meta-x-b3-flags': 'method.request.header.x-b3-flags',
                'integration.request.path.requestId': 'context.requestId',
            }
        )
        s3_integration = aws_apigateway.AwsIntegration(service='s3',
                                                       integration_http_method="PUT",
                                                       path=f'{bucket.bucket_name}/{s3_key_prefix}/{{requestId}}-request.json',
                                                       options=integration_options)
        apigw.root.add_resource(path).add_method('POST', s3_integration,
                                                 method_responses=[aws_apigateway.MethodResponse(status_code='202')],
                                                 request_parameters={
                                                     'method.request.header.Content-Type': False,
                                                     'method.request.header.b3': False,
                                                     'method.request.header.x-b3-traceid': False,
                                                     'method.request.header.x-b3-spanid': False,
                                                     'method.request.header.x-b3-sampled': False,
                                                     'method.request.header.x-b3-flags': False,
                                                 })


app = core.App()
CdkStack(app, STACK_NAME, env={'region': 'eu-west-1'})

app.synth()
