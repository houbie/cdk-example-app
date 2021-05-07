from aws_cdk import aws_lambda, core, aws_s3, aws_s3_notifications
from aws_cdk.aws_s3 import EventType, NotificationKeyFilter

from cdk_lib.string_utils import snake

DEFAULT_RUNTIME = aws_lambda.Runtime.PYTHON_3_8


def lambda_function(scope: core.Construct, name: str, **kwargs) -> aws_lambda.Function:
    """Creates a :py:class:`aws_lambda.Function` with default arguments"""
    defaults = {
        'function_name': f'{name}-fn',
        'runtime': DEFAULT_RUNTIME,
        'code': scope.code_asset('cdk_example_app'),
        'handler': f'{snake(name)}_lambda/{snake(name)}.handler',
        'layers': getattr(scope, 'lambda_layers', []),
    }

    function_id = name.title() + 'Handler'
    return aws_lambda.Function(scope, function_id, **defaults, **kwargs)


def s3_event_handler(scope: core.Construct, name: str,
                     bucket: aws_s3.Bucket,
                     *filters: NotificationKeyFilter,
                     s3_key_prefix=None,
                     event: EventType = aws_s3.EventType.OBJECT_CREATED,
                     **kwargs) -> aws_lambda.Function:
    event_handler = lambda_function(scope, name, **kwargs)
    if s3_key_prefix and not filters:
        filters = [aws_s3.NotificationKeyFilter(prefix=s3_key_prefix)]
    bucket.add_event_notification(
        event,
        aws_s3_notifications.LambdaDestination(event_handler),
        *filters
    )
    return event_handler
