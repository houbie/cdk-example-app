import * as cdk from '@aws-cdk/core'
import * as CdkExampleApp from '../lib/cdk-example-app-stack'
import '@aws-cdk/assert/jest'

test('CdkExampleAppStack', () => {
    const app = new cdk.App()
    // WHEN
    new CdkExampleApp.CdkExampleAppStack(app, 'CdkExampleAppStack')
    const stack = app.synth().getStackByName('CdkExampleAppStack')
    // THEN
    expect(stack).toHaveResource('AWS::DynamoDB::Table', {TableName: 'event-log'})
    expect(stack).toHaveResource('AWS::Lambda::Function', {FunctionName: 'api-fn'})
    expect(stack).toHaveResource('AWS::S3::Bucket')
    expect(stack).toHaveResource('AWS::Lambda::Function', {FunctionName: 's3-integration-event-fn'})
    expect(stack).toHaveResource('AWS::ApiGateway::RestApi', {
        Name: 'CdkExampleApi',
        EndpointConfiguration: {Types: ['REGIONAL']}
    })
    expect(stack).toHaveResource('AWS::ApiGateway::Resource', {PathPart: 's3-integration-event'})
})
