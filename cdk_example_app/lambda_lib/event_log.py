import os
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone, timedelta

from aws_lambda_powertools import Logger
from botocore.session import Session
from pynamodb.attributes import UnicodeAttribute, UTCDateTimeAttribute, BooleanAttribute, TTLAttribute
from pynamodb.indexes import GlobalSecondaryIndex, AllProjection
from pynamodb.models import Model

EVENT_LOG_TTL = timedelta(days=1)

STATUS_PROCESSING = 'PROCESSING'
STATUS_DONE = 'DONE'
STATUS_FAILED = 'FAILED'


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
        table_name = os.environ.get("EVENT_LOG_TABLE", "event-log")
        host = os.environ.get('DYNAMODB_HOST')
        region = Session().get_config_variable("region")

    id = UnicodeAttribute(hash_key=True)
    status = UnicodeAttribute()
    s3_key = UnicodeAttribute(attr_name='key')
    s3_bucket = UnicodeAttribute(attr_name='bucket')
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
            if getattr(self, 'logger'):
                self.logger.info('processed s3 object')

    def mark_failed(self, error: str):
        if not self.processed_time:
            self.processed_time = datetime.now(timezone.utc)
            self.error = str(error)
            self.status = STATUS_FAILED
            self.save()
            if getattr(self, 'logger'):
                self.logger.warning(f'processing s3 object failed: {error}')


@contextmanager
def event_log(s3_bucket: str, s3_key: str, function_name: str, logger: Logger) -> EventLog:
    logger.append_keys(s3_bucket=s3_bucket, s3_key=s3_key)
    logger.debug(f"processing s3 event")
    log = EventLog(
        id=str(uuid.uuid4()),
        status=STATUS_PROCESSING,
        s3_key=s3_key,
        s3_bucket=s3_bucket,
        function=function_name,
        region=os.environ.get('AWS_REGION', 'no region set'),
        received_time=datetime.now(timezone.utc),  # TODO get from s3 record
    )
    log.logger = logger
    log.save()
    try:
        yield log
        log.mark_processed()
    except Exception as e:
        if logger.log_level == 'DEBUG':
            logger.exception(f"error processing s3 object")
        log.mark_failed(str(e))
        raise
