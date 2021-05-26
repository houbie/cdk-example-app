from aws_lambda_powertools import Logger

from cdk_example_app.lambda_lib.event_log import event_log, EventLog
from test.compare import assert_similar

logger = Logger(service='event-log-test')


def test_with_event_log(event_log_table):
    with event_log('my-bucket', 'my-key', 'my-lambda', logger) as event_log_:
        log_id = event_log_.id
        event_log_.set_functional_key('funky', 'music')

    assert_similar(EventLog.get(log_id).attribute_values, {
        'id': log_id,
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
        with event_log('my-bucket', 'my-key', 'my-lambda', logger) as event_log_:
            log_id = event_log_.id
            event_log_.set_functional_key('funky', 'music')
            raise ValueError('my-error')
        assert False
    except ValueError:
        assert True

    assert_similar(EventLog.get(log_id).attribute_values, {
        'id': log_id,
        'function': 'my-lambda',
        's3_bucket': 'my-bucket',
        's3_key': 'my-key',
        'functional_key_name': 'funky',
        'functional_key_value': 'music',
        'gzip': False,
        'region': 'no region set',
        'status': 'FAILED',
        'error': 'my-error',
    })
    # TODO check logger output
