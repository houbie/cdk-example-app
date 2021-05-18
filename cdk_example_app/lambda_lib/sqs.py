import inspect
import json
from functools import wraps, lru_cache
from json import JSONDecodeError
from typing import Callable

import boto3
from aws_lambda_powertools import Logger

from cdk_example_app.lambda_lib.tracing.sqs_propagation import sqs_trace_propagator, start_sqs_root_span

logger = Logger()


@lru_cache
def sqs_client():
    client = boto3.client('sqs')
    client.send_message = sqs_trace_propagator(client.send_message)
    return client


def send_json(obj, **kwargs):
    sqs_client().send_message(MessageBody=json.dumps(obj), **kwargs)


def sqs_json_event_handler(func: Callable):
    handler_params = inspect.signature(func).parameters.keys()
    record_arg = 'record' in handler_params
    context_arg = 'context' in handler_params
    func_name = f'{inspect.getmodule(func)}.{func.__name__}'

    @wraps(func)
    def wrapper(event, context):
        logger.info({'message': 'sqs_json_event_handler', 'records': len(event['Records'])})
        for record in event['Records']:
            try:
                with start_sqs_root_span(func_name, record):
                    args = {}
                    if record_arg:
                        args['record'] = record
                    if context_arg:
                        args['context'] = context
                    return func(json.loads(record['body']), **args)  # TODO make parsing optional
            except Exception as e:
                logger.error({
                    'error': 'Exception while handling SQS record',
                    'message': str(e),
                })
                # don't re-throw exception in case of invalid JSON because lambda retry will fail again
                if type(e) != JSONDecodeError:
                    raise

    return wrapper
