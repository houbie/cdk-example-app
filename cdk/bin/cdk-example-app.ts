#!/usr/bin/env node
import 'source-map-support/register'
import * as cdk from '@aws-cdk/core'
import {CdkExampleAppStack} from '../lib/cdk-example-app-stack'

const app = new cdk.App()
new CdkExampleAppStack(app, 'CdkExampleApp-eu-west-1', {
    // specialize this stack for the AWS Account and Region that are implied by the current CLI configuration
    env: {account: process.env.CDK_DEFAULT_ACCOUNT, region: 'eu-west-1'}
})

new CdkExampleAppStack(app, 'CdkExampleApp-eu-central-1', {
    // specialize this stack for the AWS Account and Region that are implied by the current CLI configuration
    env: {account: process.env.CDK_DEFAULT_ACCOUNT, region: 'eu-central-1'}
})
