from __future__ import absolute_import
import logging
import time
from typing import Optional
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from requests.exceptions import ReadTimeout
from urllib3.exceptions import ReadTimeoutError
from flask import has_request_context, request, current_app
import urllib.parse as urlparse

from . import __version__
from .errors import APIError, HTTPError, InvalidResponse
from .exceptions import ImproperlyConfigured


logger = logging.getLogger(__name__)


def make_iter_method(method_name, *model_names):
    """Make a page-concatenating iterator method from a find method

    :param method_name: The name of the find method to decorate
    :param model_names: The names of the possible models as they appear in the JSON response. The first found is used.
    """
    def iter_method(self, *args, **kwargs):
        result = getattr(self, method_name)(*args, **kwargs)
        # Filter the list of model names for those that are a key in the response, then take the first.
        # Useful for backwards compatability if response keys might change
        model_name = next((model_name for model_name in model_names if model_name in result), None)
        # If there are no model names, return None to avoid raising StopIteration
        if not model_name:
            return

        for model in result[model_name]:
            yield model

        while True:
            if 'next' not in result.get('links', {}):
                return

            result = self._get(result['links']['next'])
            for model in result[model_name]:
                yield model

    return iter_method


class classproperty(object):
    def __init__(self, getter):
        self.getter = getter

    def __get__(self, instance, owner):
        return self.getter(owner)


class BaseAPIClient(object):
    _RETRIES = 5
    _RETRIES_BACKOFF_FACTOR = 0.3
    #  Respose status codes to retry on.
    _RETRIES_FORCE_STATUS_CODES = (500, 502, 503, 504)

    # the following are really intended to be read-only from outside the class, hence properties
    @classproperty
    def RETRIES(cls):
        return cls._RETRIES

    @classproperty
    def RETRIES_BACKOFF_FACTOR(cls):
        return cls._RETRIES_BACKOFF_FACTOR

    @classproperty
    def RETRIES_FORCE_STATUS_CODES(cls):
        return cls._RETRIES_FORCE_STATUS_CODES

    @property
    def base_url(self):
        return self._base_url

    @property
    def auth_token(self):
        return self._auth_token

    @property
    def enabled(self):
        return self._enabled

    @property
    def timeout(self):
        return self._timeout

    @property
    def nowait_timeout(self):
        read_timeout = 1.e-3
        try:
            return self.timeout[0], read_timeout
        except (TypeError, LookupError):
            return self._timeout, read_timeout

    def __init__(self, base_url=None, auth_token=None, enabled=True, timeout=(15, 45,), *, user=None):
        self._base_url = base_url
        self._auth_token = auth_token
        self._user = user
        self._enabled = enabled
        self._timeout = timeout

    def _getuser(self, user=None):
        if user is None and self._user is None:
            raise ValueError(
                "you must provide a user for updated_by, either in the API client constructor or in each method call"
            )
        elif user is None:
            return self._user
        else:
            return user

    def _patch(self, url, data, *, client_wait_for_response: bool = True):
        return self._request("PATCH", url, data=data, client_wait_for_response=client_wait_for_response)

    def _patch_with_updated_by(self, url, data, *, user: Optional[str] = None, client_wait_for_response: bool = True):
        user = self._getuser(user)
        data = dict(data, updated_by=user)
        return self._patch(url, data, client_wait_for_response=client_wait_for_response)

    def _put(self, url, data, *, client_wait_for_response: bool = True):
        return self._request("PUT", url, data=data, client_wait_for_response=client_wait_for_response)

    def _put_with_updated_by(self, url, data, *, user: Optional[str] = None, client_wait_for_response: bool = True):
        user = self._getuser(user)
        data = dict(data, updated_by=user)
        return self._put(url, data, client_wait_for_response=client_wait_for_response)

    def _get(self, url, params=None, *, client_wait_for_response: bool = True):
        return self._request("GET", url, params=params, client_wait_for_response=client_wait_for_response)

    def _post(self, url, data, *, client_wait_for_response: bool = True):
        return self._request("POST", url, data=data, client_wait_for_response=client_wait_for_response)

    def _post_with_updated_by(self, url, data, *, user: Optional[str] = None, client_wait_for_response: bool = True):
        user = self._getuser(user)
        data = dict(data, updated_by=user)
        return self._post(url, data, client_wait_for_response=client_wait_for_response)

    def _delete(self, url, data=None, *, client_wait_for_response: bool = True):
        return self._request("DELETE", url, data=data, client_wait_for_response=client_wait_for_response)

    def _delete_with_updated_by(self, url, data, *, user: Optional[str] = None, client_wait_for_response: bool = True):
        user = self._getuser(user)
        data = dict(data, updated_by=user)
        return self._delete(url, data, client_wait_for_response=client_wait_for_response)

    def _build_url(self, url, params):
        if not self._base_url:
            raise ImproperlyConfigured("{} has no URL configured".format(self.__class__.__name__))

        url = urlparse.urljoin(self._base_url, url)

        # Make sure we always preserve the base_url host and scheme
        # eg when using next link from the API response we need to keep the scheme
        # so that app requests don't try to switch from HTTP to HTTPS
        url = urlparse.urlparse(url)
        base_url = urlparse.urlparse(self._base_url)
        url = url._replace(netloc=base_url.netloc, scheme=base_url.scheme).geturl()

        r = requests.PreparedRequest()
        r.prepare_url(url=url, params=params)

        return r.url

    def _requests_retry_session(self, *, retry_read_timeouts: bool = True):
        session = requests.Session()
        # TODO: remove ignore once requests' typeshed entry is correct (currently missing status and raise_on_status).
        retry = Retry(  # type: ignore
            total=self._RETRIES,
            read=self._RETRIES if retry_read_timeouts else 0,
            connect=self._RETRIES,
            status=self._RETRIES,
            backoff_factor=self._RETRIES_BACKOFF_FACTOR,
            status_forcelist=self._RETRIES_FORCE_STATUS_CODES,
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        return session

    @staticmethod
    def _iter_exceptions_by_cause(exc):
        yield exc
        while True:
            if getattr(exc, "__cause__", None) is not None:
                exc = exc.__cause__
            # you might have hoped that PEP 3134 would have successfully standardized this and we could stop
            # here, but no - many exceptions thrown up by requests/urllib3 have nonstandard ways of chaining exceptions:
            elif getattr(exc, "reason", None) is not None:
                exc = exc.reason
            elif getattr(exc, "args", None) is not None and len(exc.args) and isinstance(exc.args[0], BaseException):
                exc = exc.args[0]
            else:
                break

            yield exc

    def _request(self, method, url, data=None, params=None, *, client_wait_for_response: bool = True):
        if not self._enabled:
            return None

        url = self._build_url(url, params)
        headers = {
            "Content-type": "application/json",
            "Authorization": "Bearer {}".format(self._auth_token),
            "User-agent": "DM-API-Client/{}".format(__version__),
        }
        if has_request_context():
            # Disable type checking for attributes added by RequestIdRequestMixin - mypy doesn't know about it.
            if callable(getattr(request, "get_onwards_request_headers", None)):
                headers.update(request.get_onwards_request_headers())  # type: ignore
            elif getattr(request, "request_id", None) and current_app.config.get("DM_REQUEST_ID_HEADER"):
                # support old .request_id attr for compatibility
                headers[current_app.config["DM_REQUEST_ID_HEADER"]] = request.request_id  # type: ignore

        # not using CaseInsensitiveDict as our header dict initially as technically .update()'s behaviour is undefined
        # for it, but past a certain point we want to be able to know we've resolved what our final header value is
        # going to be for any certain header name
        ci_headers = requests.structures.CaseInsensitiveDict(headers)
        # just in case anyone misses the point and thinks adding anything more to `headers` will do anything beyond here
        del headers

        # determine our final outgoing span id - find the first of DM_SPAN_ID_HEADERS which is set to something truthy
        child_span_id = next(
            (
                ci_headers[header_name] for header_name in (current_app.config.get("DM_SPAN_ID_HEADERS") or ())
                if ci_headers.get(header_name)
            ),
            None,
        ) if has_request_context() else None

        common_log_extra = {
            **({"childSpanId": child_span_id} if child_span_id is not None else {}),
        }

        logger.log(
            logging.DEBUG,
            "API request {method} {url}",
            extra={
                **common_log_extra,
                'method': method,
                'url': url,
            },
        )

        start_time = time.perf_counter()
        try:
            response = self._requests_retry_session(retry_read_timeouts=client_wait_for_response).request(
                method,
                url,
                headers=ci_headers,
                json=data,
                timeout=self.timeout if client_wait_for_response else self.nowait_timeout,
            )
            response.raise_for_status()
        except requests.RequestException as e:
            elapsed_time = time.perf_counter() - start_time

            # requests appears quite variable in what exceptions it will actually provide given a certain error,
            # depending on e.g. whether retries are enabled, so we need to be quite flexible in detecting ReadTimeout
            if (not client_wait_for_response) and any(
                isinstance(exc, (ReadTimeout, ReadTimeoutError)) for exc in self._iter_exceptions_by_cause(e)
            ):
                logger.log(
                    logging.INFO,
                    "API {api_method} request on {api_url} dispatched but ignoring response",
                    extra={
                        **common_log_extra,
                        'api_method': method,
                        'api_url': url,
                        'api_time': elapsed_time,
                        'api_time_incomplete': True,
                    },
                )
                return None

            api_error = HTTPError.create(e)
            logger.log(
                logging.INFO if api_error.status_code == 404 else logging.WARNING,
                "API {api_method} request on {api_url} failed with {api_status} '{api_error}'",
                extra={
                    **common_log_extra,
                    'api_method': method,
                    'api_url': url,
                    'api_status': api_error.status_code,
                    'api_error': '{} raised {}'.format(api_error.message, str(e)),
                    'api_time': elapsed_time,
                },
            )
            raise api_error
        else:
            elapsed_time = time.perf_counter() - start_time
            logger.log(
                logging.INFO,
                "API {api_method} request on {api_url} finished in {api_time}",
                extra={
                    **common_log_extra,
                    'api_method': method,
                    'api_url': url,
                    'api_status': response.status_code,
                    'api_time': elapsed_time,
                },
            )
        try:
            return response.json()
        except ValueError:
            raise InvalidResponse(response,
                                  message="No JSON object could be decoded")

    def get_status(self):
        try:
            return self._get("{}/_status".format(self._base_url))
        except APIError as e:
            try:
                return e.response.json()
            except (ValueError, AttributeError):
                return {
                    "status": "error",
                    "message": "{}".format(e.message),
                }
