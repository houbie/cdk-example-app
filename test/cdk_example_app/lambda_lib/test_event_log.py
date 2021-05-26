from aws_lambda_powertools import Logger

from cdk_example_app.lambda_lib.event_log import event_log, EventLog
from test.compare import assert_similar

logger = Logger(service='event-log-test')


def test_with_event_log(event_log_table):
    with event_log('my-bucket', 'my-key', 'my-lambda', logger) as event_log_:
        event_log_.set_functional_key('funky', 'music')

    assert_similar(EventLog.get('my-key').attribute_values, {
        'function': 'my-lambda',
        's3_bucket': 'my-bucket',
        's3_key': 'my-key',
        'functional_key_name': 'funky',
        'functional_key_value': 'music',
        'gzip': False,
        'region': 'no region set',
        'status': 'DONE',
    })
    # TODO check logger output


def test_with_event_log_raising_exception(event_log_table):
    try:
        with event_log('my-bucket', 'my-error-key', 'my-lambda', logger) as event_log_:
            event_log_.set_functional_key('funky', 'music')
            raise ValueError('my-error')
        assert False
    except ValueError:
        assert True

    assert_similar(EventLog.get('my-error-key').attribute_values, {
        'function': 'my-lambda',
        's3_bucket': 'my-bucket',
        's3_key': 'my-error-key',
        'functional_key_name': 'funky',
        'functional_key_value': 'music',
        'gzip': False,
        'region': 'no region set',
        'status': 'FAILED',
        'error': 'my-error',
    })
    # TODO check logger output
