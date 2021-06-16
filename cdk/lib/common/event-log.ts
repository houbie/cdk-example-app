import {Construct, RemovalPolicy} from "@aws-cdk/core"
import {AttributeType, Table} from "@aws-cdk/aws-dynamodb"


export function createEventLogTable(scope: Construct): Table {
    return new Table(scope, 'EventLogTable', {
        tableName: 'event-log',
        partitionKey: {name: 'id', type: AttributeType.STRING},
        removalPolicy: RemovalPolicy.DESTROY
    })
}
