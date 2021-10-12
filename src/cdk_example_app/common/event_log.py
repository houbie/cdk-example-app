import os
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone

from aws_lambda_powertools import Logger
from botocore.session import Session
from pynamodb.attributes import (
    BooleanAttribute,
    TTLAttribute,
    UnicodeAttribute,
    UTCDateTimeAttribute,
)
from pynamodb.indexes import AllProjection, GlobalSecondaryIndex
from pynamodb.models import Model

EVENT_LOG_TTL = timedelta(days=1)

STATUS_PROCESSING = "PROCESSING"
STATUS_DONE = "DONE"
STATUS_FAILED = "FAILED"


class StatusIndex(GlobalSecondaryIndex):
    class Meta:
        # All attributes are projected
        projection = AllProjection()
        read_capacity_units = 1000
        write_capacity_units = 1000

    status = UnicodeAttribute(hash_key=True)


class EventLog(Model):
    """Event processing log"""

    class Meta:
        table_name = os.environ.get("EVENT_LOG_TABLE", f"event-log-{os.environ['AWS_REGION']}")

    s3_key = UnicodeAttribute(hash_key=True)
    s3_bucket = UnicodeAttribute(attr_name="bucket")
    status = UnicodeAttribute()
    gzip = BooleanAttribute(default=False)
    function = UnicodeAttribute()
    region = UnicodeAttribute()
    functional_key_name = UnicodeAttribute(null=True, attr_name="funcKeyName")
    functional_key_value = UnicodeAttribute(null=True, attr_name="funcKeyVal")
    trace_id = UnicodeAttribute(null=True, attr_name="trace")
    received_time = UTCDateTimeAttribute(attr_name="received")
    processed_time = UTCDateTimeAttribute(null=True, attr_name="processed")
    error = UnicodeAttribute(null=True)
    expires = TTLAttribute(default_for_new=EVENT_LOG_TTL)

    status_index = StatusIndex()

    def set_functional_key(self, functional_key_name: str, functional_key_value: str):
        self.functional_key_name = functional_key_name
        self.functional_key_value = functional_key_value

    def mark_processed(self):
        if not self.processed_time:
            self.processed_time = datetime.now(timezone.utc)
            self.status = STATUS_DONE
            self.save()
            if self.logger:
                self.logger.info("processed s3 object")

    def mark_failed(self, error: str):
        if not self.processed_time:
            self.processed_time = datetime.now(timezone.utc)
            self.error = str(error)
            self.status = STATUS_FAILED
            self.save()
            if self.logger:
                self.logger.warning(f"processing s3 object failed: {error}")


@contextmanager
def event_log(s3_bucket: str, s3_key: str, function_name: str, logger: Logger) -> EventLog:
    logger.append_keys(s3_bucket=s3_bucket, s3_key=s3_key)
    logger.debug("processing s3 event")
    log = EventLog(
        status=STATUS_PROCESSING,
        s3_key=s3_key,
        s3_bucket=s3_bucket,
        function=function_name,
        region=os.environ.get("AWS_REGION", "eu-west-1"),
        received_time=datetime.now(timezone.utc),  # TODO get from s3 record
    )
    # pylint: disable=attribute-defined-outside-init
    log.logger = logger
    log.save()
    try:
        yield log
        log.mark_processed()
    except Exception as e:
        if logger.log_level == "DEBUG":
            logger.exception("error processing s3 object")
        log.mark_failed(str(e))
        raise
