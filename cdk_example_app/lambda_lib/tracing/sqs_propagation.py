import typing
from contextlib import contextmanager
from functools import wraps

from opentelemetry import propagate
from opentelemetry.propagators.b3 import B3Format
from opentelemetry.propagators.textmap import Getter
from opentelemetry.trace import SpanKind, Span

from cdk_example_app.lambda_lib.tracing import tracer


def _message_attribute_setter(message_attributes, key, value):
    message_attributes[key] = {'StringValue': value, 'DataType': 'String'}


def sqs_trace_propagator(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        message_attributes = kwargs.get('MessageAttributes', {})
        B3Format().inject(_message_attribute_setter, message_attributes)
        kwargs['MessageAttributes'] = message_attributes
        return func(*args, **kwargs)

    return wrapper


class _MessageAttributeGetter(Getter):
    def get(self, message_attributes, key: str):
        return [message_attributes.get(key, {}).get('stringValue')]

    def keys(self, message_attributes):
        return list(message_attributes.keys())


@contextmanager
def start_sqs_root_span(name: str,
                        sqs_record,
                        kind: SpanKind = SpanKind.SERVER,
                        end_on_exit: bool = True,
                        **kwargs) -> typing.Iterator['Span']:
    ctx = propagate.extract(_MessageAttributeGetter(), sqs_record.get('messageAttributes', {}))
    with tracer.start_as_current_span(name, context=ctx, kind=kind, end_on_exit=end_on_exit, **kwargs) as span:
        yield span
