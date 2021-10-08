import {Function, Runtime} from "@aws-cdk/aws-lambda"
import {Duration, Stack} from "@aws-cdk/core"
import {kebab, snake, title} from "./string-utils"
import {FunctionProps} from "@aws-cdk/aws-lambda/lib/function"
import {PythonStack} from "./stack"
import {Table} from "@aws-cdk/aws-dynamodb"
import {Bucket, EventType, NotificationKeyFilter} from "@aws-cdk/aws-s3"
import {LambdaDestination} from "@aws-cdk/aws-s3-notifications"

const DEFAULT_RUNTIME = Runtime.PYTHON_3_8


function createPythonLambda(stack: PythonStack, name: string, options?: FunctionProps): Function {
    const defaults: FunctionProps = {
        functionName: `${kebab(name)}-fn`,
        runtime: DEFAULT_RUNTIME,
        timeout: Duration.seconds(30),
        code: stack.createCodeAsset('src'),
        handler: `${snake(Stack.of(stack).stackName)}.${snake(name)}_lambda.handler`,
        layers: stack.lambdaLayers,
        environment: {
            LOG_LEVEL: 'INFO',
            POWERTOOLS_SERVICE_NAME: name
        }
    }

    const functionId = title(name) + 'Handler'
    return new Function(stack, functionId, {...defaults, ...options})
}

interface S3EventHandlerProps {
    bucket: Bucket,
    filters?: NotificationKeyFilter[],
    s3KeyPrefix?: string,
    event?: EventType,
    eventLogTable?: Table,
    functionProps?: FunctionProps
}

function createS3EventHandler(stack: PythonStack, name: string, props: S3EventHandlerProps): Function {
    const eventHandler = createPythonLambda(stack, name, props.functionProps)
    let {
        event = EventType.OBJECT_CREATED,
        filters = [],
        bucket,
        eventLogTable,
        s3KeyPrefix
    } = props

    if (s3KeyPrefix && !filters) {
        filters = [{prefix: props.s3KeyPrefix}]
    }

    bucket.addEventNotification(event, new LambdaDestination(eventHandler), ...filters)
    bucket.grantRead(eventHandler)
    if (eventLogTable) {
        eventLogTable.grantReadWriteData(eventHandler)
        eventLogTable.grant(eventHandler, 'dynamodb:DescribeTable')
    }
    return eventHandler
}

export {
    createPythonLambda,
    createS3EventHandler
}
