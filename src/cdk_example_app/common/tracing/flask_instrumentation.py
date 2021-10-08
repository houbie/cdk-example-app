import os
from typing import List

from flask import Flask


def instrument(app: Flask, excludes: List[str] = None) -> Flask:
    # set env variable before importing FlaskInstrumentor
    if excludes:
        os.environ["OTEL_PYTHON_FLASK_EXCLUDED_URLS"] = ",".join(excludes)

    # pylint: disable=import-outside-toplevel
    from opentelemetry.instrumentation.flask import FlaskInstrumentor

    FlaskInstrumentor().instrument_app(app)
    return app
