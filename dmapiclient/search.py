import six

from .base import BaseAPIClient
from .errors import HTTPError


class SearchAPIClient(BaseAPIClient):
    def init_app(self, app):
        self.base_url = app.config['DM_SEARCH_API_URL']
        self.auth_token = app.config['DM_SEARCH_API_AUTH_TOKEN']
        self.enabled = app.config['ES_ENABLED']

    def _url(self, index, path):
        return u"/{}/services/{}".format(index, path)

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

    def _add_filters_to_params(self, params, filters):
        """In-place transformation of filter keys and storage in params."""
        for filter_name, filter_values in six.iteritems(filters):
            params[u'filter_{}'.format(filter_name)] = filter_values

    def search_services(self, index, q=None, page=None, **filters):
        params = {}
        if q is not None:
            params['q'] = q

        if page:
            params['page'] = page

        self._add_filters_to_params(params, filters)

        response = self._get(self._url(index, "search"), params=params)
        return response

    def aggregate_services(self, index, q=None, aggregations=[], **filters):
        params = {}
        if q is not None:
            params['q'] = q

        self._add_filters_to_params(params, filters)

        params['aggregations'] = aggregations

        response = self._get(self._url(index, "aggregations"), params=params)
        return response
