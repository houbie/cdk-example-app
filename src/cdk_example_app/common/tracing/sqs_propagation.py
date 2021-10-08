from contextlib import contextmanager
from functools import wraps
from typing import Iterator

from opentelemetry import propagate
from opentelemetry.context import Context
from opentelemetry.propagators.b3 import B3MultiFormat
from opentelemetry.propagators.textmap import Getter
from opentelemetry.trace import Span, SpanKind

from cdk_example_app.common.tracing.tracer import tracer


def _message_attribute_setter(message_attributes, key, value):
    message_attributes[key] = {"StringValue": value, "DataType": "String"}


def sqs_trace_propagator(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        message_attributes = kwargs.get("MessageAttributes", {})
        B3MultiFormat().inject(_message_attribute_setter, Context(message_attributes))
        kwargs["MessageAttributes"] = message_attributes
        return func(*args, **kwargs)

    return wrapper


class _MessageAttributeGetter(Getter):
    def get(self, carrier, key: str):
        return [carrier.get(key, {}).get("stringValue")]

    def keys(self, carrier):
        return list(carrier.keys())


@contextmanager
def start_sqs_root_span(
    name: str, sqs_record, kind: SpanKind = SpanKind.SERVER, end_on_exit: bool = True, **kwargs
) -> Iterator[Span]:
    ctx = propagate.extract(_MessageAttributeGetter(), sqs_record.get("messageAttributes", {}))
    with tracer.start_as_current_span(name, context=ctx, kind=kind, end_on_exit=end_on_exit, **kwargs) as span:
        yield span
