import {AwsIntegration, EndpointType, IntegrationOptions, PassthroughBehavior, RestApi} from "@aws-cdk/aws-apigateway"
import {Bucket} from "@aws-cdk/aws-s3"
import {Role, ServicePrincipal} from "@aws-cdk/aws-iam"
import {RestApiProps} from "@aws-cdk/aws-apigateway/lib/restapi"
import {Construct} from "@aws-cdk/core"


export interface S3IntegrationProps {
    bucket: Bucket,
    s3KeyPrefix?: string,
    s3KeySuffix?: string,
    httpMethod?: string,
    role?: Role
}

export class RestApiWithDefaults extends RestApi {
    constructor(scope: Construct, construct_id: string, props?: RestApiProps) {
        super(scope, construct_id, {endpointConfiguration: {types: [EndpointType.REGIONAL], ...props}})
    }

    addS3Integration(path: string, props: S3IntegrationProps): void {
        const role = props.role || this.addS3IntegrationRole(props.bucket)
        const s3KeyPrefix = props.s3KeyPrefix || path
        const s3KeySuffix = props.s3KeyPrefix || '-request.json'
        const httpMethod = props.httpMethod || 'POST'

        const {
            s3AwsIntegration,
            integrationOptions
        } = this.createS3AwsIntegration(props.bucket.bucketName, s3KeyPrefix, s3KeySuffix, role)
        this.root.resourceForPath(path).addMethod(httpMethod, s3AwsIntegration, {
            methodResponses: [{statusCode: '202'}],
            requestParameters: {
                'method.request.header.Content-Type': false,
                'method.request.header.b3': false,
                'method.request.header.x-b3-traceid': false,
                'method.request.header.x-b3-spanid': false,
                'method.request.header.x-b3-sampled': false,
                'method.request.header.x-b3-flags': false
            }
        })
        this.latestDeployment?.addToLogicalId({
            path: `${props.bucket.bucketName}/${s3KeyPrefix}/{requestId}${s3KeySuffix}`,
            'integration_responses': integrationOptions.integrationResponses,
            'request_parameters': integrationOptions.requestParameters,
        })
    }

    createS3AwsIntegration(bucketName: string, s3KeyPrefix: string, s3KeySuffix: string, role: Role)
        : { s3AwsIntegration: AwsIntegration, integrationOptions: IntegrationOptions } {
        const integrationOptions: IntegrationOptions = {
            credentialsRole: role,
            integrationResponses: [{
                statusCode: '202',
                selectionPattern: '2\\d{2}',
                responseTemplates: {'application/json': '{"requestId": "$context.requestId"}'}
            }],
            passthroughBehavior: PassthroughBehavior.WHEN_NO_MATCH,
            requestParameters: {
                'integration.request.header.Content-Type': 'method.request.header.Content-Type',
                // we can save headers as as meta data on the S3 object
                'integration.request.header.x-amz-meta-b3': 'method.request.header.b3',
                'integration.request.header.x-amz-meta-x-b3-traceid': 'method.request.header.x-b3-traceid',
                'integration.request.header.x-amz-meta-x-b3-spanid': 'method.request.header.x-b3-spanid',
                'integration.request.header.x-amz-meta-x-b3-sampled': 'method.request.header.x-b3-sampled',
                'integration.request.header.x-amz-meta-x-b3-flags': 'method.request.header.x-b3-flags',
                'integration.request.path.requestId': 'context.requestId',
            }
        }
        const s3AwsIntegration = new AwsIntegration({
            service: 's3',
            integrationHttpMethod: 'PUT',
            path: `${bucketName}/${s3KeyPrefix}/{requestId}${s3KeySuffix}`,
            options: integrationOptions
        })
        return {s3AwsIntegration, integrationOptions}
    }

    addS3IntegrationRole(bucket: Bucket): Role {
        const role = new Role(this, `${bucket.node.id}ApigwRole`, {
            assumedBy: new ServicePrincipal('apigateway.amazonaws.com').grantPrincipal
        })
        bucket.grantReadWrite(role)
        return role
    }
}
