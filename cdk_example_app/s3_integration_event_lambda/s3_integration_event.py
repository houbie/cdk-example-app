from aws_lambda_powertools import Logger

from cdk_example_app.lambda_lib.s3 import s3_event_handler

logger = Logger()


def functional_key_extractor(**kwargs):
    pass


@s3_event_handler(logger, functional_key_extractor=functional_key_extractor, parse_json=True)
def handler(json_body, **kwargs):
    logger.info({"message": 'Received Json from S3', 'body': json_body})
