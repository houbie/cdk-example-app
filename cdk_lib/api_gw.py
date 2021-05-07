from typing import Tuple

from aws_cdk import aws_apigateway, aws_iam, aws_s3, core


class RestApi(aws_apigateway.RestApi):
    def __init__(self, scope: core.Construct, construct_id: str, **kwargs) -> None:
        defaults = {
            'endpoint_configuration': aws_apigateway.EndpointConfiguration(types=[aws_apigateway.EndpointType.REGIONAL])
        }
        super().__init__(scope, construct_id, **defaults, **kwargs)

    def add_s3_integration(self, path: str, *,
                           bucket: aws_s3.Bucket,
                           s3_key_prefix: str = None,
                           http_method: str = 'POST',
                           s3_key_suffix: str = '-request.json',
                           role: aws_iam.Role = None,
                           ) -> None:
        if not role:
            role = self.add_s3_integration_role(bucket)
        if not s3_key_prefix:
            s3_key_prefix = path

        s3_integration, s3_integration_options = self.s3_aws_integration(bucket.bucket_name, s3_key_prefix, role)
        self.root.resource_for_path(path).add_method(http_method, s3_integration,
                                                     method_responses=[
                                                         aws_apigateway.MethodResponse(status_code='202')],
                                                     request_parameters={
                                                         'method.request.header.Content-Type': False,
                                                         'method.request.header.b3': False,
                                                         'method.request.header.x-b3-traceid': False,
                                                         'method.request.header.x-b3-spanid': False,
                                                         'method.request.header.x-b3-sampled': False,
                                                         'method.request.header.x-b3-flags': False,
                                                     })
        self.latest_deployment.add_to_logical_id({
            'path': f'{bucket.bucket_name}/{s3_key_prefix}/{{requestId}}{s3_key_suffix}',
            'integration_responses': s3_integration_options.integration_responses,
            'request_parameters': s3_integration_options.request_parameters,
        })

    @staticmethod
    def s3_aws_integration(bucket_name: str, s3_key_prefix: str, role: aws_iam.Role
                           ) -> Tuple[aws_apigateway.AwsIntegration, aws_apigateway.IntegrationOptions]:
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
        aws_integration = aws_apigateway.AwsIntegration(service='s3',
                                                        integration_http_method="PUT",
                                                        path=f'{bucket_name}/{s3_key_prefix}/{{requestId}}-request.json',
                                                        options=integration_options)
        return aws_integration, integration_options

    def add_s3_integration_role(self, bucket: aws_s3.Bucket) -> aws_iam.Role:
        role = aws_iam.Role(self, f'{bucket.node.id}ApigwRole',
                            assumed_by=aws_iam.ServicePrincipal('apigateway.amazonaws.com').grant_principal)
        bucket.grant_read_write(role)
        return role
