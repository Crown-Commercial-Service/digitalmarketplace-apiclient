import pytest
import requests_mock
from flask import Flask


@pytest.fixture
def app():
    return Flask(__name__)


@pytest.yield_fixture
def rmock():
    with requests_mock.mock() as rmock:
        real_register_uri = rmock.register_uri

        def register_uri_with_complete_qs(*args, **kwargs):
            if 'complete_qs' not in kwargs:
                kwargs['complete_qs'] = True

            return real_register_uri(*args, **kwargs)

        rmock.register_uri = register_uri_with_complete_qs

        yield rmock
