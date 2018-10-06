from flask import Flask

try:
    import ujson as json
except ImportError:
    import json


def json_response(body, status_code=200, content_type="application/json"):
    """
    Encodes the provided body to JSON and returns a Flask JSON response object
    """
    return Flask.response_class(
        response=json.dumps(body),
        status=status_code,
        content_type=content_type
    )


def id_name_pair(id, name, **kwargs):
    """
    Takes an id/name pair as positional arguments and returns a dict.
    Extra arguments can also be provided
    """
    return {
        "id": id,
        "name": name,
        **kwargs
    }