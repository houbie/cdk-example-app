import connexion
from flask import jsonify


def create_app(name, specification, specification_dir, base_path=None, options=None, resolver=None):
    """Create a connexion app with swagger_ui disabled by default"""

    if options is None:
        options = {"swagger_ui": False}

    connexion_app = connexion.FlaskApp(name, specification_dir=specification_dir, options=options)
    connexion_app.add_api(specification, base_path=base_path, resolver=resolver)

    # TODO instrument flask app
    return connexion_app


def info():
    # TODO
    return jsonify("TODO")
