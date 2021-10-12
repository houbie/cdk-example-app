import * as cdk from '@aws-cdk/core'
import {RemovalPolicy} from '@aws-cdk/core'
import {RestApiWithDefaults} from "./common/api-gw"
import {LambdaIntegration} from "@aws-cdk/aws-apigateway"
import {createEventLogTable} from "./common/event-log"
import {createPythonLambda, createS3EventHandler} from "./common/lambda-function"
import {PythonStack} from "./common/stack"
import {Bucket} from "@aws-cdk/aws-s3"

const S3_EVENT_PATH = 's3-integration-event'


function getBucketName(region: string): string {
    const user = process.env.USER?.toLowerCase() || Math.floor(Math.random() * 1000)
    return `${user}-cdk-example-app-events-${region}`
}

export class CdkExampleAppStack extends PythonStack {
    constructor(scope: cdk.Construct, id: string, props?: cdk.StackProps) {
        super(scope, id, props)

        const region = cdk.Stack.of(this).region
        const eventLogTable = createEventLogTable(this, region)

        const apiLambda = createPythonLambda(this, 'Api')

        const events_bucket = new Bucket(this, "EventsBucket", {
            bucketName: getBucketName(region),
            removalPolicy: RemovalPolicy.DESTROY,
            autoDeleteObjects: true
        })
        createS3EventHandler(this, 'S3IntegrationEvent', {
            bucket: events_bucket,
            s3KeyPrefix: S3_EVENT_PATH,
            eventLogTable: eventLogTable
        })

        const apiGw = new RestApiWithDefaults(this, 'CdkExampleApi')
        apiGw.root.addProxy({defaultIntegration: new LambdaIntegration(apiLambda)})
        apiGw.addS3Integration(S3_EVENT_PATH, {bucket: events_bucket})
    }
}
