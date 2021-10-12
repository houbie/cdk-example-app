import json
import logging
import os

import serverless_wsgi
from connexion import ProblemException
from connexion.apps.flask_app import FlaskApp
from connexion.security.security_handler_factory import AbstractSecurityHandlerFactory
from flask import Response, jsonify


def render_problem_exception(error):
    """Custom error renderer that adheres to the Nike REST API guidelines"""
    result = {"message": error.title}
    if error.detail:
        result["errors"] = [error.detail]
    result["code"] = error.type if error.type else "VALIDATION_ERROR"
    return Response(response=json.dumps(result), status=error.status, mimetype="application/json")


def _disable_connexion_security():
    # Connexion wraps all operations with a security check
    # We modify the decorator to just return the original operation without wrapping it
    AbstractSecurityHandlerFactory.verify_security = lambda cls, auth_funcs, required_scopes, function: function
    logging.getLogger("connexion.operations.secure").setLevel(logging.ERROR)


def create_app(
    name,
    specification,
    specification_dir="./",
    base_path=None,
    options=None,
    resolver=None,
    error_renderer=render_problem_exception,
):
    """Create a connexion app with swagger_ui disabled by default"""

    if options is None:
        options = {"swagger_ui": False}
    _disable_connexion_security()
    connexion_app = FlaskApp(name, specification_dir=specification_dir, options=options)
    connexion_app.app.url_map.strict_slashes = False
    connexion_app.add_api(specification, base_path=base_path, resolver=resolver)
    serverless_wsgi.TEXT_MIME_TYPES.append("application/problem+json")  # mimetype of connexion validation errors
    connexion_app.add_error_handler(ProblemException, error_renderer)

    # TODO instrument flask app
    return connexion_app


def info():
    try:
        with open(
            os.path.join(os.environ.get("LAMBDA_TASK_ROOT", "./"), "generated/app-info.json"), "r", encoding="utf-8"
        ) as file:
            app_info = json.load(file)
            app_info["region"] = os.environ.get("AWS_REGION", "?")
        return jsonify(app_info)
    except FileNotFoundError:
        return jsonify("No app-info.json found. Make sure to generate it during the build?")
