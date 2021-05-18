import json
from functools import lru_cache, wraps
from json import JSONDecodeError
from typing import Callable

import boto3
from aws_lambda_powertools import Logger
from opentelemetry.trace import Status, StatusCode, format_trace_id

from cdk_example_app.lambda_lib.event_log import event_log
from cdk_example_app.lambda_lib.tracing.s3_propagation import start_s3_root_span


@lru_cache
def s3_client():
    return boto3.client('s3')


def get_json(bucket: str, key: str) -> object:
    s3_obj = s3_client().get_object(Bucket=bucket, Key=key)
    return json.load(s3_obj['Body']), s3_obj["Metadata"]


def s3_event_handler(logger: Logger, functional_key_extractor: Callable = None, parse_json=False) -> Callable:
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(event, context):
            for record in event['Records']:
                s3_bucket = record['s3']['bucket']['name']
                s3_key = record['s3']['object']['key']

                with event_log(s3_bucket, s3_key, context.function_name, logger) as event_log_:
                    s3_obj = s3_client().get_object(Bucket=s3_bucket, Key=s3_key)
                    with start_s3_root_span(context.function_name, s3_obj, s3_bucket, s3_key) as span:
                        trace_id = format_trace_id(span.get_span_context().trace_id)
                        logger.append_keys(traceId=trace_id)
                        event_log_.trace_id = trace_id
                        # TODO: gzip support
                        if parse_json:
                            try:
                                body = json.loads(s3_obj['Body'])
                            except JSONDecodeError as e:
                                msg = f'S3 object {s3_key} in bucket {s3_bucket} is not valid Json: {e}'
                                event_log_.mark_failed(msg)
                                span.set_status(Status(StatusCode.ERROR, msg))
                                continue
                        else:
                            body = s3_obj['Body'].decode(s3_obj.get('ContentEncoding', 'utf-8'))

                        if functional_key_extractor:
                            functional_key_name, functional_key_value = functional_key_extractor(body)
                            logger.append_keys(**{functional_key_name: functional_key_value})
                            span.set_attribute(functional_key_name, functional_key_value)
                            event_log_.set_functional_key(functional_key_name, functional_key_value)

                        # invoke wrapped function
                        func(body, s3_obj=s3_obj, record=record)

        return wrapper

    return decorator


def foo():
    return s3_client().get_object(Bucket='s3_bucket', Key='s3_key')
