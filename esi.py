import requests


def get(url, *args, **kwargs):
    """Pass GET request to ESI"""
    return requests.get("https://esi.evetech.net%s?datasource=tranquility" % url, *args, **kwargs)