# -*- coding: utf-8 -*-
from contextlib import contextmanager
import logging

from flask import request
import requests
import requests_mock
import pytest
import mock

from dmtestutils.comparisons import RestrictedAny

from dmapiclient.base import BaseAPIClient
from dmapiclient import HTTPError, InvalidResponse
from dmapiclient.errors import REQUEST_ERROR_STATUS_CODE
from dmapiclient.exceptions import ImproperlyConfigured

from urllib3.exceptions import NewConnectionError, ProtocolError


@pytest.yield_fixture
def raw_rmock():
    with mock.patch('dmapiclient.base.requests.request') as rmock:
        yield rmock


@pytest.fixture
def base_client():
    return BaseAPIClient('http://baseurl', 'auth-token', True)


@contextmanager
def _empty_context_manager():
    yield


class TestBaseApiClient(object):
    def _from_httplib_response_mock(self, status, response_data=None):
        response_mock = mock.Mock(
            status=status, headers={}, spec=['get_redirect_location', 'getheader', 'read', 'reason']
        )
        response_mock.get_redirect_location.return_value = None
        response_mock.getheader.return_value = None
        response_mock.read.side_effect = [response_data, None, None]
        response_mock.reason = f'Mocked {status} response'

        return response_mock

    @pytest.mark.parametrize(('retry_count'), range(1, 4))
    @mock.patch('urllib3.connectionpool.HTTPConnectionPool._make_request')
    @mock.patch('dmapiclient.base.BaseAPIClient.RETRIES_BACKOFF_FACTOR', 0)
    def test_client_retries_on_connection_error_and_raises_api_error(self, _make_request, base_client, retry_count):
        _make_request.side_effect = NewConnectionError(mock.Mock(), 'Im a message')

        with mock.patch('dmapiclient.base.BaseAPIClient.RETRIES', retry_count):
            with pytest.raises(HTTPError) as e:
                base_client._request("GET", '/')

        requests = _make_request.call_args_list

        assert len(requests) == retry_count + 1
        assert all((request[0][1], request[0][2]) == ('GET', '/') for request in requests)

        assert 'ConnectionError' in e.value.message
        assert e.value.status_code == REQUEST_ERROR_STATUS_CODE

    @pytest.mark.parametrize(('retry_count'), range(1, 4))
    @mock.patch('urllib3.connectionpool.HTTPConnectionPool._make_request')
    @mock.patch('dmapiclient.base.BaseAPIClient.RETRIES_BACKOFF_FACTOR', 0)
    def test_client_retries_on_read_error_and_raises_api_error(self, _make_request, base_client, retry_count):
        _make_request.side_effect = ProtocolError(mock.Mock(), 'Im a message')

        with mock.patch('dmapiclient.base.BaseAPIClient.RETRIES', retry_count):
            with pytest.raises(HTTPError) as e:
                base_client._request("GET", '/')

        requests = _make_request.call_args_list

        assert len(requests) == retry_count + 1
        assert all((request[0][1], request[0][2]) == ('GET', '/') for request in requests)

        assert 'ProtocolError' in e.value.message
        assert e.value.status_code == REQUEST_ERROR_STATUS_CODE

    @pytest.mark.parametrize(('retry_count'), range(1, 4))
    @pytest.mark.parametrize(('status'), BaseAPIClient.RETRIES_FORCE_STATUS_CODES)
    @mock.patch('urllib3.connectionpool.HTTPConnectionPool.ResponseCls.from_httplib')
    @mock.patch('urllib3.connectionpool.HTTPConnectionPool._make_request')
    @mock.patch('dmapiclient.base.BaseAPIClient.RETRIES_BACKOFF_FACTOR', 0)
    def test_client_retries_on_http_error_and_raises_api_error(
        self, _make_request, from_httplib, base_client, status, retry_count
    ):
        response_mock = self._from_httplib_response_mock(status)
        from_httplib.return_value = response_mock

        with mock.patch('dmapiclient.base.BaseAPIClient.RETRIES', retry_count):
            with pytest.raises(HTTPError) as e:
                base_client._request("GET", '/')

        requests = _make_request.call_args_list

        assert len(requests) == retry_count + 1
        assert all((request[0][1], request[0][2]) == ('GET', '/') for request in requests)

        assert f'{status} Server Error: {response_mock.reason} for url: http://baseurl/\n' in e.value.message
        assert e.value.status_code == status

    @mock.patch('urllib3.connectionpool.HTTPConnectionPool.ResponseCls.from_httplib')
    @mock.patch('urllib3.connectionpool.HTTPConnectionPool._make_request')
    @mock.patch('dmapiclient.base.BaseAPIClient.RETRIES_BACKOFF_FACTOR', 0)
    def test_client_retries_and_returns_data_if_successful(self, _make_request, from_httplib, base_client):
        #  The third response here would normally be a httplib response object. It's only use is to be passed in to
        #  `from_httplib`, which we're mocking the return of below. `from_httplib` converts a httplib response into a
        #  urllib3 response. The mock object we're returning is a mock for that urllib3 response.
        _make_request.side_effect = [
            ProtocolError(mock.Mock(), '1st error'),
            ProtocolError(mock.Mock(), '2nd error'),
            ProtocolError(mock.Mock(), '3nd error'),
            'httplib_response - success!',
        ]

        from_httplib.return_value = self._from_httplib_response_mock(200, response_data=b'{"Success?": "Yes!"}')

        response = base_client._request("GET", '/')
        requests = _make_request.call_args_list

        assert len(requests) == 4
        assert all((request[0][1], request[0][2]) == ('GET', '/') for request in requests)
        assert response == {'Success?': 'Yes!'}

    def test_non_2xx_response_raises_api_error(self, base_client, rmock):
        rmock.request(
            "GET",
            "http://baseurl/",
            json={"error": "Not found"},
            status_code=404)

        with pytest.raises(HTTPError) as e:
            base_client._request("GET", '/')

        assert e.value.message == "Not found"
        assert e.value.status_code == 404

    def test_base_error_is_logged(self, base_client):
        with requests_mock.Mocker() as m:
            m.register_uri('GET', '/', exc=requests.RequestException())

            with pytest.raises(HTTPError) as e:
                base_client._request("GET", "/")

            assert e.value.message == "\nRequestException()"
            assert e.value.status_code == 503

    def test_invalid_json_raises_api_error(self, base_client, rmock):
        rmock.request(
            "GET",
            "http://baseurl/",
            text="Internal Error",
            status_code=200)

        with pytest.raises(InvalidResponse) as e:
            base_client._request("GET", '/')

        assert e.value.message == "No JSON object could be decoded"
        assert e.value.status_code == 200

    def test_user_agent_is_set(self, base_client, rmock):
        rmock.request(
            "GET",
            "http://baseurl/",
            json={},
            status_code=200)

        base_client._request('GET', '/')

        assert rmock.last_request.headers.get("User-Agent").startswith("DM-API-Client/")

    def test_request_always_uses_base_url_scheme(self, base_client, rmock):
        rmock.request(
            "GET",
            "http://baseurl/path/",
            json={},
            status_code=200)

        base_client._request('GET', 'https://host/path/')
        assert rmock.called

    def test_null_api_throws(self):
        bad_client = BaseAPIClient(None, 'auth-token', True)
        with pytest.raises(ImproperlyConfigured):
            bad_client._request('GET', '/anything')

    def test_onwards_request_headers_added_if_available(self, base_client, rmock, app):
        rmock.get("http://baseurl/_status", json={"status": "ok"}, status_code=200)
        with app.test_request_context('/'):
            # add a simple mock callable instead of using a full request implementation
            request.get_onwards_request_headers = mock.Mock()
            request.get_onwards_request_headers.return_value = {
                "Douce": "bronze",
                "Kennedy": "gold",
            }

            base_client.get_status()

            assert rmock.last_request.headers["Douce"] == "bronze"
            assert rmock.last_request.headers["kennedy"] == "gold"

            assert request.get_onwards_request_headers.call_args_list == [
                # just a single, arg-less call
                (),
            ]

    def test_onwards_request_headers_not_available(self, base_client, rmock, app):
        rmock.get("http://baseurl/_status", json={"status": "ok"}, status_code=200)
        with app.test_request_context('/'):
            # really just asserting no exception arose from performing a call without get_onwards_request_headers being
            # available
            base_client.get_status()

    def test_request_id_fallback(self, base_client, rmock, app):
        # request.request_id is an old interface which we're still supporting here just for compatibility
        rmock.get("http://baseurl/_status", json={"status": "ok"}, status_code=200)
        app.config["DM_REQUEST_ID_HEADER"] = "Bar"
        with app.test_request_context('/'):
            request.request_id = "Ormond"

            base_client.get_status()

            assert rmock.last_request.headers["bar"] == "Ormond"

    @pytest.mark.parametrize("dm_span_id_headers_setting", (None, ("X-Brian-Tweedy", "Major-Tweedy",),))
    @pytest.mark.parametrize("has_request_context", (False, True),)
    @mock.patch("dmapiclient.base.logger")
    def test_child_span_id_not_provided(
        self,
        logger,
        dm_span_id_headers_setting,
        has_request_context,
        base_client,
        rmock,
        app,
    ):
        rmock.get("http://baseurl/_status", json={"status": "ok"}, status_code=200)
        app.config["DM_SPAN_ID_HEADERS"] = dm_span_id_headers_setting
        with (app.test_request_context('/') if has_request_context else _empty_context_manager()):
            if has_request_context:
                request.get_onwards_request_headers = mock.Mock(return_value={
                    "impression": "arrested",
                })

            base_client.get_status()

            assert rmock.called
            assert logger.log.call_args_list == [
                mock.call(logging.DEBUG, "API request {method} {url}", extra={
                    "method": "GET",
                    "url": "http://baseurl/_status",
                    # childSpanId NOT provided
                }),
                mock.call(logging.INFO, "API {api_method} request on {api_url} finished in {api_time}", extra={
                    "api_method": "GET",
                    "api_url": "http://baseurl/_status",
                    "api_status": 200,
                    "api_time": mock.ANY,
                    # childSpanId NOT provided
                }),
            ]

    @pytest.mark.parametrize("onwards_request_headers", (
        {
            "X-Brian-Tweedy": "Amiens Street",
        },
        {
            "major-TWEEDY": "Amiens Street",
        },
        {
            "Major-Tweedy": "terminus",
            "x-brian-tweedy": "Amiens Street",
        },
        {
            # note same header name, different capitalizations
            "X-BRIAN-TWEEDY": "great northern",
            "x-brian-tweedy": "Amiens Street",
        },
    ))
    @pytest.mark.parametrize("response_status", (200, 500,))
    @mock.patch("dmapiclient.base.logger")
    def test_child_span_id_provided(
        self,
        mock_logger,
        onwards_request_headers,
        response_status,
        base_client,
        rmock,
        app,
    ):
        rmock.get("http://baseurl/_status", json={"status": "foobar"}, status_code=response_status)
        app.config["DM_SPAN_ID_HEADERS"] = ("X-Brian-Tweedy", "major-tweedy",)
        with app.test_request_context('/'):
            request.get_onwards_request_headers = mock.Mock(return_value=onwards_request_headers)

            try:
                base_client.get_status()
            except HTTPError:
                # it is tested elsewhere whether this exception is raised in the *right* circumstances or not
                pass

            assert rmock.called

            # some of our scenarios test multiple header names differing only by capitalization - we care that the same
            # span id that was chosen for the log message is the same one that was sent in the onwards request header,
            # so we need two distinct values which are acceptable
            either_span_id = RestrictedAny(lambda value: value == "Amiens Street" or value == "great northern")

            assert mock_logger.log.call_args_list == [
                mock.call(logging.DEBUG, "API request {method} {url}", extra={
                    "method": "GET",
                    "url": "http://baseurl/_status",
                    "childSpanId": either_span_id,
                }),
                (
                    mock.call(
                        logging.INFO,
                        "API {api_method} request on {api_url} finished in {api_time}", extra={
                            "api_method": "GET",
                            "api_url": "http://baseurl/_status",
                            "api_status": response_status,
                            "api_time": mock.ANY,
                            "childSpanId": either_span_id,
                        }
                    ) if response_status == 200 else mock.call(
                        logging.WARNING,
                        "API {api_method} request on {api_url} failed with {api_status} '{api_error}'", extra={
                            "api_method": "GET",
                            "api_url": "http://baseurl/_status",
                            "api_status": response_status,
                            "api_time": mock.ANY,
                            "api_error": mock.ANY,
                            "childSpanId": either_span_id,
                        },
                    )
                )
            ]
            # both logging calls should have had the *same* childSpanId value
            assert mock_logger.log.call_args_list[0][1]["extra"]["childSpanId"] \
                == mock_logger.log.call_args_list[1][1]["extra"]["childSpanId"]

            # that value should be the same one that was sent in the onwards request header
            assert (
                rmock.last_request.headers.get("x-brian-tweedy")
                or rmock.last_request.headers.get("major-tweedy")
            ) == mock_logger.log.call_args_list[0][1]["extra"]["childSpanId"]
