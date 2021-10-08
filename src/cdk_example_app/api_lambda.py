#!/usr/bin/env python

import serverless_wsgi

from cdk_example_app.common.connexion.application_factory import create_app

app = create_app(__name__, "openApi.yaml").app


def handler(event, context):
    return serverless_wsgi.handle_request(app, event, context)


if __name__ == "__main__":
    app.run(port=8080)
