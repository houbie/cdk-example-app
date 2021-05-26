from aws_cdk import aws_dynamodb, core
from aws_cdk.aws_dynamodb import Attribute


def event_log_table(scope: core.Construct):
    return aws_dynamodb.Table(scope, 'EventLogTable',
                              table_name='event-log',
                              partition_key=Attribute(name='id', type=aws_dynamodb.AttributeType.STRING))
