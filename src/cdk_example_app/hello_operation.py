from flask import jsonify


def hello_world():
    return jsonify(greeting='Hello world!')
