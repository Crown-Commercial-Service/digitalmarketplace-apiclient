# -*- coding: utf-8 -*-

import re
import six
try:
    from urllib.parse import urlparse, parse_qsl
except ImportError:
    from urlparse import urlparse, parse_qsl


from .base import BaseAPIClient
from .errors import HTTPError


class SearchAPIClient(BaseAPIClient):
    def init_app(self, app):
        self.base_url = app.config['DM_SEARCH_API_URL']
        self.auth_token = app.config['DM_SEARCH_API_AUTH_TOKEN']
        self.enabled = app.config['ES_ENABLED']

    def _url(self, index, path):
        return u"/{}/services/{}".format(index, path)

    def _url_reverse(self, url):
        url = urlparse(url)
        try:
            index, path = re.match(r'^/(?P<index>.+)/services/(?P<path>.+)$', url.path).groups()
        except AttributeError:
            return None, None
        else:
            return index, path

    def _add_filters_prefix_to_params(self, params, filters):
        """In-place transformation of filter keys and storage in params."""
        for filter_name, filter_values in six.iteritems(filters):
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

    def get_url(self, path, index, q, page=None, aggregations=[], **filters):
        params = {}
        if q is not None:
            params['q'] = q

        if aggregations:
            params['aggregations'] = aggregations
        elif page:
            params['page'] = page

        self._add_filters_prefix_to_params(params, filters)

        return self._build_url(url=self._url(index=index, path=path), params=params)

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

    def get_search_url(self, index, q=None, page=None, **filters):
        return self.get_url(path='search', index=index, q=q, page=page, **filters)

    def get_aggregations_url(self, index, q=None, aggregations=[], **filters):
        return self.get_url(path='aggregations', index=index, q=q, aggregations=aggregations, **filters)

    def create_index(self, index):
        return self._put(
            '/{}'.format(index),
            data={'type': 'index'}
        )

    def set_alias(self, alias_name, target_index):
        return self._put(
            '/{}'.format(alias_name),
            data={'type': 'alias', 'target': target_index}
        )

    def index(self, index, service_id, service):
        url = self._url(index, service_id)
        return self._put(url, data={'service': service})

    def delete(self, index, service_id):
        url = self._url(index, service_id)

        try:
            return self._delete(url)
        except HTTPError as e:
            if e.status_code != 404:
                raise
        return None

    def search_services(self, index, q=None, page=None, **filters):
        response = self._get(self.get_search_url(index=index,
                                                 q=q,
                                                 page=page,
                                                 **filters))

        return response

    def aggregate_services(self, index, q=None, aggregations=[], **filters):
        response = self._get(self.get_aggregations_url(index=index,
                                                       q=q,
                                                       aggregations=aggregations,
                                                       **filters))
        return response
