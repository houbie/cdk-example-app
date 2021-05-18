import re
from dataclasses import dataclass
from unittest.mock import Mock

import pytest
from opentelemetry.trace import SpanKind, format_trace_id

import cdk_example_app.lambda_lib.s3 as s3
from cdk_example_app.lambda_lib.event_log import EventLog, STATUS_DONE, STATUS_FAILED
from test.compare import assert_similar, ignore

TRACE_ID = '80f198ee56343ba864fe8b2a57d3eff7'
SPAN_ID = '05e3ac9a4f6e3b90'


@dataclass
class Context:
    function_name: str


@pytest.fixture
def create_event_handler(event_log_table):
    def create(parse_json=True):
        handler_args = []
        logger = Mock()

        @s3.s3_event_handler(logger, parse_json=parse_json)
        def handler(body, s3_obj, record):
            if 'handler-error' in record['s3']['object']['key']:
                raise Exception(record['s3']['object']['key'])
            handler_args.append({'body': body, 's3_obj': s3_obj, 'record': record})

        return handler, handler_args, logger

    return create


@pytest.fixture
def s3_get_object_mock(mocker):
    s3_client = mocker.patch('cdk_example_app.lambda_lib.s3.s3_client')
    get_object = s3_client.return_value.get_object

    def respond(Bucket, Key):
        if 'exception' in Key:
            raise Exception(Key)

        metadata = {}
        if 'trace' in Key:
            metadata = {
                'x-b3-traceid': TRACE_ID,
                'x-b3-spanid': SPAN_ID,
                'x-b3-sampled': '1',

            }
        if 'json' in Key:
            return {
                'Body': b'{"foo":"bar"}',
                'Metadata': metadata
            }
        return {
            'Body': b'foo bar',
            'Metadata': metadata
        }

    get_object.side_effect = respond
    return get_object


@pytest.fixture
def create_s3_event():
    def create(keys):
        records = [
            {'s3': {
                'bucket': {'name': 'my-bucket'},
                'object': {'key': key},
            }} for key in keys
        ]

        return {'Records': records}

    return create


def test_s3_event_handler(create_event_handler, s3_get_object_mock, create_s3_event):
    handler, handler_args, _ = create_event_handler(parse_json=False)
    event = create_s3_event(['my-key'])
    handler(event, Context(function_name='my-lambda'))

    assert handler_args == [{'body': 'foo bar',
                             'record': {'s3': {'bucket': {'name': 'my-bucket'},
                                               'object': {'key': 'my-key'}}},
                             's3_obj': {'Body': b'foo bar', 'Metadata': {}}}]
    s3_get_object_mock.assert_called_once_with(Bucket='my-bucket', Key='my-key')


def test_json_s3_event_handler(create_event_handler, s3_get_object_mock, create_s3_event):
    handler, handler_args, _ = create_event_handler()
    event = create_s3_event(['my-json-key'])
    handler(event, Context(function_name='my-lambda'))

    assert handler_args == [{'body': {'foo': 'bar'},
                             'record': {'s3': {'bucket': {'name': 'my-bucket'},
                                               'object': {'key': 'my-json-key'}}},
                             's3_obj': {'Body': b'{"foo":"bar"}', 'Metadata': {}}}]
    s3_get_object_mock.assert_called_once_with(Bucket='my-bucket', Key='my-json-key')


def test_s3_event_handler_trace_propagation(create_event_handler, s3_get_object_mock, create_s3_event, mocker):
    trace_export = mocker.patch('cdk_example_app.lambda_lib.tracing.tracer.logger_span_exporter.export')
    handler, handler_args, _ = create_event_handler()
    event = create_s3_event(['my-key-with-parse-error', 'my-json-key-with-trace'])
    handler(event, Context(function_name='my-lambda'))

    span_1 = trace_export.call_args_list[0].args[0][0]
    assert span_1.attributes == {'s3Bucket': 'my-bucket', 's3Key': 'my-key-with-parse-error'}
    assert format_trace_id(span_1.context.trace_id) != TRACE_ID
    assert span_1.kind == SpanKind.SERVER
    assert not span_1.status.is_ok
    assert span_1.status.description == 'S3 object my-key-with-parse-error in bucket my-bucket is not valid Json: ' \
                                        'Expecting value: line 1 column 1 (char 0)'

    span_2 = trace_export.call_args_list[1].args[0][0]
    assert span_2.attributes == {'s3Bucket': 'my-bucket', 's3Key': 'my-json-key-with-trace'}
    assert format_trace_id(span_2.context.trace_id) == TRACE_ID
    assert span_2.kind == SpanKind.SERVER
    assert span_2.status.is_ok


def test_s3_event_handler_event_log(create_event_handler, s3_get_object_mock, create_s3_event):
    handler, handler_args, _ = create_event_handler()
    event = create_s3_event(['my-key-with-parse-error', 'my-json-key-with-trace'])
    handler(event, Context(function_name='my-lambda'))

    done = [it for it in EventLog.status_index.query(STATUS_DONE)]
    assert len(done) == 1
    assert_similar(done[0].attribute_values, {
        'function': 'my-lambda',
        'gzip': False,
        'region': 'no region set',
        's3_bucket': 'my-bucket',
        's3_key': 'my-json-key-with-trace',
        'status': STATUS_DONE,
        'trace_id': TRACE_ID,
    })

    failed = [it for it in EventLog.status_index.query(STATUS_FAILED)]
    assert len(failed) == 1
    assert_similar(failed[0].attribute_values, {
        'function': 'my-lambda',
        'gzip': False,
        'region': 'no region set',
        's3_bucket': 'my-bucket',
        's3_key': 'my-key-with-parse-error',
        'status': STATUS_FAILED,
        'error': 'S3 object my-key-with-parse-error in bucket my-bucket is not valid '
                 'Json: Expecting value: line 1 column 1 (char 0)',
    })


def test_s3_event_handler_logging(create_event_handler, s3_get_object_mock, create_s3_event):
    handler, handler_args, logger = create_event_handler()
    event = create_s3_event(['my-key-with-parse-error', 'my-json-key-with-trace'])
    handler(event, Context(function_name='my-lambda'))

    assert_similar(logger.method_calls, [
        ('append_keys', ignore, {'s3_bucket': 'my-bucket', 's3_key': 'my-key-with-parse-error'}),
        ('debug', ('processing s3 event',)),
        ('append_keys', ignore, {'traceId': re.compile(r'\w{32}')}),
        ('warning', ('processing s3 object failed: S3 object my-key-with-parse-error in bucket '
                     'my-bucket is not valid Json: Expecting value: line 1 column 1 (char 0)',)),
        ('append_keys', ignore, {'s3_bucket': 'my-bucket', 's3_key': 'my-json-key-with-trace'}),
        ('debug', ('processing s3 event',)),
        ('append_keys', ignore, {'traceId': TRACE_ID}),
        ('info', ('processed s3 object',))
    ])


def test_s3_event_handler_with_s3_exception(create_event_handler, s3_get_object_mock, create_s3_event):
    handler, handler_args, logger = create_event_handler()
    event = create_s3_event(['my-json-key', 'my-key-with-exception'])
    with pytest.raises(Exception, match='my-key-with-exception'):
        handler(event, Context(function_name='my-lambda'))

    done = [it for it in EventLog.status_index.query(STATUS_DONE)]
    assert len(done) == 1
    assert_similar(done[0].attribute_values, {
        'function': 'my-lambda',
        'gzip': False,
        'region': 'no region set',
        's3_bucket': 'my-bucket',
        's3_key': 'my-json-key',
        'status': STATUS_DONE,
        'trace_id': re.compile(r'\w{32}'),
    })

    failed = [it for it in EventLog.status_index.query(STATUS_FAILED)]
    assert len(failed) == 1
    assert_similar(failed[0].attribute_values, {
        'function': 'my-lambda',
        'gzip': False,
        'region': 'no region set',
        's3_bucket': 'my-bucket',
        's3_key': 'my-key-with-exception',
        'status': STATUS_FAILED,
        'error': 'my-key-with-exception',
    })


def test_s3_event_handler_with_handler_exception(create_event_handler, s3_get_object_mock, create_s3_event):
    handler, handler_args, logger = create_event_handler()
    event = create_s3_event(['my-json-key', 'my-json-key-with-handler-error-and-trace'])
    with pytest.raises(Exception, match='my-json-key-with-handler-error-and-trace'):
        handler(event, Context(function_name='my-lambda'))

    done = [it for it in EventLog.status_index.query(STATUS_DONE)]
    assert len(done) == 1
    assert_similar(done[0].attribute_values, {
        'function': 'my-lambda',
        'gzip': False,
        'region': 'no region set',
        's3_bucket': 'my-bucket',
        's3_key': 'my-json-key',
        'status': STATUS_DONE,
        'trace_id': re.compile(r'\w{32}'),
    })

    failed = [it for it in EventLog.status_index.query(STATUS_FAILED)]
    assert len(failed) == 1
    assert_similar(failed[0].attribute_values, {
        'function': 'my-lambda',
        'gzip': False,
        'region': 'no region set',
        's3_bucket': 'my-bucket',
        's3_key': 'my-json-key-with-handler-error-and-trace',
        'status': STATUS_FAILED,
        'error': 'my-json-key-with-handler-error-and-trace',
        'trace_id': TRACE_ID,
    })
