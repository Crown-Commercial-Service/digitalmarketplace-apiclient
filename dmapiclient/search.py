# -*- coding: utf-8 -*-

import re
import warnings

from urllib.parse import urlparse, urlencode, urlunparse, parse_qsl

from .base import BaseAPIClient, make_iter_method
from .errors import HTTPError


class SearchAPIClient(BaseAPIClient):
    def init_app(self, app):
        self._base_url = app.config['DM_SEARCH_API_URL']
        self._auth_token = app.config['DM_SEARCH_API_AUTH_TOKEN']
        self._enabled = app.config['ES_ENABLED']

    def _url(self, index, path, doc_type='services'):
        return u"/{}/{}/{}".format(index, doc_type, path)

    def _url_reverse(self, url):
        url = urlparse(url)
        try:
            index, object_type, path = re.match(
                r'^/(?P<index>[^/]+)/(?P<object_type>[^/]+)/(?P<path>[^/]+)$',
                url.path
            ).groups()
        except AttributeError:
            return None, None, None
        else:
            return index, object_type, path

    def _add_filters_prefix_to_params(self, params, filters):
        """In-place transformation of filter keys and storage in params."""
        for filter_name, filter_values in filters.items():
            params[u'filter_{}'.format(filter_name)] = filter_values

    def _remove_filters_prefix_from_params(self, search_api_params):
        """
        Convert searchAPI url parameters to frontend url parameters by removing filter_ prefix from url parameters
        :param search_api_params: list of two item tuples
        :return: list of two item tuples
        """
        frontend_params = []
        for filter_name, filter_value in search_api_params:
            if filter_name.startswith('filter_'):
                frontend_params.append((filter_name[7:], filter_value))
            else:
                frontend_params.append((filter_name, filter_value))

        return frontend_params

    def get_url(self, path, index, q, doc_type='services', page=None, aggregations=[], id_only=False, **filters):
        params = {}
        if q is not None:
            params['q'] = q

        if aggregations:
            params['aggregations'] = aggregations
        elif page:
            params['page'] = page

        if id_only:
            params['idOnly'] = id_only

        self._add_filters_prefix_to_params(params, filters)

        return self._build_url(url=self._url(index=index, path=path, doc_type=doc_type), params=params)

    def get_frontend_params_from_search_api_url(self, search_api_url):
        """
        Converts a searchAPI url to url params a frontend understands
        :param search_api_url: Fully qualified searchAPI url
        :return: list of two item tuples [(param_name, param_value), ...]
        """
        url = urlparse(search_api_url)
        query = parse_qsl(url.query)
        frontend_params = self._remove_filters_prefix_from_params(query)

        return frontend_params

    def get_index_from_search_api_url(self, search_api_url):
        return self._url_reverse(search_api_url)[0]

    def get_search_url(self, index, q=None, page=None, doc_type='services', **filters):
        return self.get_url(path='search', index=index, doc_type=doc_type, q=q, page=page, **filters)

    def create_index(self, index, mapping):
        return self._put(
            '/{}'.format(index),
            data={'type': 'index', 'mapping': mapping}
        )

    def set_alias(self, alias_name, target_index):
        return self._put(
            '/{}'.format(alias_name),
            data={'type': 'alias', 'target': target_index}
        )

    def index(
        self,
        index_name,
        object_id,
        serialized_object,
        doc_type='services',
        *,
        client_wait_for_response: bool = True,
    ):
        url = '/{}/{}/{}'.format(index_name, doc_type, object_id)
        return self._put(url, data={'document': serialized_object}, client_wait_for_response=client_wait_for_response)

    def delete(self, index, service_id, *, client_wait_for_response: bool = True):
        url = self._url(index, service_id)

        try:
            return self._delete(url, client_wait_for_response=client_wait_for_response)
        except HTTPError as e:
            if e.status_code != 404:
                raise
        return None

    def search(self, index, doc_type, q=None, page=None, id_only=False, **filters):
        response = self._get(
            self.get_search_url(index=index, doc_type=doc_type, q=q, page=page, id_only=id_only, **filters)
        )
        return response

    def search_services_from_url(self, search_api_url, id_only=False, page=None):
        warnings.warn(
            "The output of 'search_services_from_url' is paginated. Use 'search_services_from_url_iter' instead.",
            DeprecationWarning
        )

        scheme, netloc, path, params, query, fragment = urlparse(search_api_url)

        query_params = parse_qsl(query)
        if page:
            query_params.append(('page', page))

        if id_only:
            query_params.append(('idOnly', True))

        query = urlencode(query_params)
        paged_search_api_url = urlunparse((scheme, netloc, path, params, query, fragment))

        return self._get(paged_search_api_url)

    search_services_from_url_iter = make_iter_method('search_services_from_url', 'documents', 'services')
    search_services_from_url_iter.__name__ = str("search_services_from_url_iter")

    def aggregate(self, index, doc_type, q=None, aggregations=[], **filters):
        response = self._get(
            self.get_url(path='aggregations', index=index, doc_type=doc_type, q=q, aggregations=aggregations, **filters)
        )
        return response
