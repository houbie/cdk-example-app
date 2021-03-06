from contextlib import contextmanager
from functools import wraps
from typing import Iterator

from opentelemetry import propagate
from opentelemetry.trace import Span, SpanKind

from cdk_example_app.common.tracing.tracer import tracer


def s3_trace_propagator(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        # TODO implement
        return func(*args, **kwargs)

    return wrapper


@contextmanager
def start_s3_root_span(
    name: str,
    s3_metadata: dict,
    s3_bucket: str,
    s3_key: str,
    kind: SpanKind = SpanKind.SERVER,
    end_on_exit: bool = True,
    **kwargs
) -> Iterator[Span]:
    ctx = propagate.extract(s3_metadata)
    with tracer.start_as_current_span(name, context=ctx, kind=kind, end_on_exit=end_on_exit, **kwargs) as span:
        span.set_attribute("s3Bucket", s3_bucket)
        span.set_attribute("s3Key", s3_key)
        yield span
