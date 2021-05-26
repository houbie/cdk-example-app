import typing

from aws_lambda_powertools import Logger
from opentelemetry.sdk.trace import Span
from opentelemetry.sdk.trace.export import SpanExporter, SpanExportResult
from opentelemetry.trace import format_span_id, format_trace_id

logger = Logger(service='span-exporter')


class LoggerSpanExporter(SpanExporter):
    """Implementation of :class:`SpanExporter` that logs spans as json."""

    def export(self, spans: typing.Sequence[Span]) -> SpanExportResult:
        for span in spans:
            ctx = span.get_span_context()
            span_parent = getattr(span, "parent", None)
            msg = {
                "name": span.name,
                "kind": span.kind,
                "parentSpanId": format_span_id(span_parent.span_id) if span_parent else None,
                "context": {
                    "spanId": format_span_id(ctx.span_id),
                    "traceId": format_trace_id(ctx.trace_id),
                    "sampled": ctx.trace_flags.sampled
                },
                "startTimestamp": span.start_time,
                "endTimestamp": span.end_time,
                "attributes": span.attributes,
                "status": {
                    "code": span.status.status_code,
                    "description": span.status.description
                }
            }
            logger.info(msg)
        return SpanExportResult.SUCCESS
