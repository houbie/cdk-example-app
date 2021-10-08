import pytest
from aws_lambda_powertools import Logger

from cdk_example_app.common.event_log import EventLog, event_log
from tests.compare import assert_similar

logger = Logger(service="event-log-test")


@pytest.mark.usefixtures("event_log_table")
def test_with_event_log():
    with event_log("my-bucket", "my-key", "my-lambda", logger) as event_log_:
        event_log_.set_functional_key("funky", "music")

    assert_similar(
        EventLog.get("my-key").attribute_values,
        {
            "function": "my-lambda",
            "s3_bucket": "my-bucket",
            "s3_key": "my-key",
            "functional_key_name": "funky",
            "functional_key_value": "music",
            "gzip": False,
            "region": "eu-west-1",
            "status": "DONE",
        },
    )
    # TODO check logger output


@pytest.mark.usefixtures("event_log_table")
def test_with_event_log_raising_exception():
    with pytest.raises(ValueError, match="my-error"):
        with event_log("my-bucket", "my-error-key", "my-lambda", logger) as event_log_:
            event_log_.set_functional_key("funky", "music")
            raise ValueError("my-error")

    assert_similar(
        EventLog.get("my-error-key").attribute_values,
        {
            "function": "my-lambda",
            "s3_bucket": "my-bucket",
            "s3_key": "my-error-key",
            "functional_key_name": "funky",
            "functional_key_value": "music",
            "gzip": False,
            "region": "eu-west-1",
            "status": "FAILED",
            "error": "my-error",
        },
    )
    # TODO check logger output
