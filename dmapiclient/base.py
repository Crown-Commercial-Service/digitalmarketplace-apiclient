from __future__ import absolute_import
import logging

try:
    import urlparse
except ImportError:
    import urllib.parse as urlparse

import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from flask import has_request_context, request, current_app

from monotonic import monotonic

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
        model_name = next(model_name for model_name in model_names if model_name in result)

        for model in result[model_name]:
            yield model

        while True:
            if 'next' not in result.get('links', {}):
                return

            result = self._get(result['links']['next'])
            for model in result[model_name]:
                yield model

    return iter_method


class BaseAPIClient(object):
    RETRIES = 5
    RETRIES_BACKOFF_FACTOR = 0.3
    #  Respose status codes to retry on.
    RETRIES_FORCE_STATUS_CODES = (500, 502, 503, 504)

    def __init__(self, base_url=None, auth_token=None, enabled=True, timeout=45):
        self.base_url = base_url
        self.auth_token = auth_token
        self.enabled = enabled
        self.timeout = timeout

    def _patch(self, url, data):
        return self._request("PATCH", url, data=data)

    def _patch_with_updated_by(self, url, data, user):
        data = dict(data, updated_by=user)
        return self._patch(url, data)

    def _put(self, url, data):
        return self._request("PUT", url, data=data)

    def _put_with_updated_by(self, url, data, user):
        data = dict(data, updated_by=user)
        return self._put(url, data)

    def _get(self, url, params=None):
        return self._request("GET", url, params=params)

    def _post(self, url, data):
        return self._request("POST", url, data=data)

    def _post_with_updated_by(self, url, data, user):
        data = dict(data, updated_by=user)
        return self._post(url, data)

    def _delete(self, url, data=None):
        return self._request("DELETE", url, data=data)

    def _delete_with_updated_by(self, url, data, user):
        data = dict(data, updated_by=user)
        return self._delete(url, data)

    def _build_url(self, url, params):
        if not self.base_url:
            raise ImproperlyConfigured("{} has no URL configured".format(self.__class__.__name__))

        url = urlparse.urljoin(self.base_url, url)

        # Make sure we always preserve the base_url host and scheme
        # eg when using next link from the API response we need to keep the scheme
        # so that app requests don't try to switch from HTTP to HTTPS
        url = urlparse.urlparse(url)
        base_url = urlparse.urlparse(self.base_url)
        url = url._replace(netloc=base_url.netloc, scheme=base_url.scheme).geturl()

        r = requests.PreparedRequest()
        r.prepare_url(url=url, params=params)

        return r.url

    def _requests_retry_session(self):
        session = requests.Session()
        retry = Retry(
            total=self.RETRIES,
            read=self.RETRIES,
            connect=self.RETRIES,
            status=self.RETRIES,
            backoff_factor=self.RETRIES_BACKOFF_FACTOR,
            status_forcelist=self.RETRIES_FORCE_STATUS_CODES,
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        return session

    def _request(self, method, url, data=None, params=None):
        if not self.enabled:
            return None

        url = self._build_url(url, params)
        headers = {
            "Content-type": "application/json",
            "Authorization": "Bearer {}".format(self.auth_token),
            "User-agent": "DM-API-Client/{}".format(__version__),
        }
        if has_request_context():
            if callable(getattr(request, "get_onwards_request_headers", None)):
                headers.update(request.get_onwards_request_headers())
            elif getattr(request, "request_id", None) and current_app.config.get("DM_REQUEST_ID_HEADER"):
                # support old .request_id attr for compatibility
                headers[current_app.config["DM_REQUEST_ID_HEADER"]] = request.request_id

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

        start_time = monotonic()
        try:
            response = self._requests_retry_session().request(
                method,
                url,
                headers=ci_headers,
                json=data,
                timeout=self.timeout
            )
            response.raise_for_status()
        except requests.RequestException as e:
            api_error = HTTPError.create(e)
            elapsed_time = monotonic() - start_time
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
            elapsed_time = monotonic() - start_time
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
        except ValueError as e:
            raise InvalidResponse(response,
                                  message="No JSON object could be decoded")

    def get_status(self):
        try:
            return self._get("{}/_status".format(self.base_url))
        except APIError as e:
            try:
                return e.response.json()
            except (ValueError, AttributeError):
                return {
                    "status": "error",
                    "message": "{}".format(e.message),
                }
