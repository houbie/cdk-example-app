import os

from aws_lambda_powertools import Logger
from opentelemetry import propagate, trace
from opentelemetry.instrumentation.botocore import BotocoreInstrumentor
from opentelemetry.propagators.b3 import B3MultiFormat
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.trace import Tracer, format_trace_id

from cdk_example_app.common.tracing.logger_span_exporter import LoggerSpanExporter

TRACER_SERVICE_NAME_ENV_VARIABLE = "TRACER_SERVICE_NAME"

logger = Logger()


class LoggerContextSimpleExportSpanProcessor(SimpleSpanProcessor):
    def on_start(self, span, parent_context=None):
        trace_id = format_trace_id(span.context.trace_id)
        logger.structure_logs(append=True, traceId=trace_id, correlationId=trace_id)


trace_provider = TracerProvider(
    resource=Resource.create(
        {SERVICE_NAME: os.environ.get(TRACER_SERVICE_NAME_ENV_VARIABLE, "TRACER_SERVICE_NAME_UNSPECIFIED")}
    )
)
logger_span_exporter = LoggerSpanExporter()
trace_provider.add_span_processor(LoggerContextSimpleExportSpanProcessor(logger_span_exporter))
trace.set_tracer_provider(trace_provider)
tracer: Tracer = trace.get_tracer(__name__)

propagate.set_global_textmap(B3MultiFormat())
BotocoreInstrumentor().instrument()
