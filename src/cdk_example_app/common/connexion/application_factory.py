import connexion
import serverless_wsgi
from flask import jsonify


def create_app(name, specification, specification_dir='.', base_path=None, options=None, resolver=None):
    """Create a connexion app with swagger_ui disabled by default"""

    connexion_app = connexion.FlaskApp(name, specification_dir=specification_dir, options=options)
    connexion_app.add_api(specification, base_path=base_path, resolver=resolver)
    serverless_wsgi.TEXT_MIME_TYPES.append('application/problem+json')  # mimetype of connexion validation errors

    # TODO instrument flask app
    return connexion_app


def info():
    # TODO
    return jsonify("TODO")
