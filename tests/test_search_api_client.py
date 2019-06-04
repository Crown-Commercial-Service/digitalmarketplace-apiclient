# -*- coding: utf-8 -*-
import os

from flask import json
import pytest
import mock

from dmapiclient import SearchAPIClient
from dmapiclient import APIError, HTTPError


@pytest.fixture
def search_client():
    return SearchAPIClient('http://baseurl', 'auth-token', True)


class TestSearchApiClient(object):
    def test_init_app_sets_attributes(self, search_client):
        app = mock.Mock()
        app.config = {
            "DM_SEARCH_API_URL": "http://example",
            "DM_SEARCH_API_AUTH_TOKEN": "example-token",
            "ES_ENABLED": False,
        }
        search_client.init_app(app)

        assert search_client.base_url == "http://example"
        assert search_client.auth_token == "example-token"
        assert not search_client.enabled

    def test_get_status(self, search_client, rmock):
        rmock.get(
            "http://baseurl/_status",
            json={"status": "ok"},
            status_code=200)

        result = search_client.get_status()

        assert result['status'] == "ok"
        assert rmock.called

    def test_create_index(self, search_client, rmock):
        rmock.put(
            "http://baseurl/new-index",
            json={"status": "ok"},
            status_code=200)

        result = search_client.create_index('new-index', 'some-mapping')

        assert rmock.called
        assert result['status'] == "ok"
        assert rmock.last_request.json() == {
            "type": "index",
            "mapping": "some-mapping",
        }

    def test_set_alias(self, search_client, rmock):
        rmock.put(
            "http://baseurl/new-alias",
            json={"status": "ok"},
            status_code=200)

        result = search_client.set_alias('new-alias', 'target')

        assert rmock.called
        assert result['status'] == "ok"
        assert rmock.last_request.json() == {
            "type": "alias",
            "target": 'target'
        }

    def test_post_to_index_with_type_and_id(
            self, search_client, rmock):
        rmock.put(
            'http://baseurl/briefs-digital-outcomes-and-specialists-2/briefs/12345',
            json={'message': 'acknowledged'},
            status_code=200)
        result = search_client.index(
            'briefs-digital-outcomes-and-specialists-2',
            "12345",
            {'serialized': 'brief'},
            doc_type='briefs',
        )
        assert result == {'message': 'acknowledged'}

    def test_post_to_index_without_type_defaults_to_services(
            self, search_client, rmock):
        rmock.put(
            'http://baseurl/g-cloud-9/services/12345',
            json={'message': 'acknowledged'},
            status_code=200)
        result = search_client.index(
            'g-cloud-9',
            "12345",
            {'serialized': 'service'},
        )
        assert result == {'message': 'acknowledged'}

    def test_delete_to_delete_method_service_id(
            self, search_client, rmock):
        rmock.delete(
            'http://baseurl/g-cloud/services/12345',
            json={"services": {
                "_id": "12345",
                "_index": "g-cloud",
                "_type": "services",
                "_version": 1,
                "found": True
            }},
            status_code=200)
        result = search_client.delete(index='g-cloud', service_id="12345")
        assert result['services']['found'] is True

    def test_delete_raises_if_http_error_not_404(
            self, search_client, rmock):
        rmock.delete(
            'http://baseurl/g-cloud/services/12345',
            json={"services": {
                "_id": "12345",
                "_index": "g-cloud",
                "_type": "services",
                "_version": 1,
                "found": True
            }},
            status_code=400)
        with pytest.raises(HTTPError):
            search_client.delete(index='g-cloud', service_id="12345")

    def test_delete_returns_none_if_404(
            self, search_client, rmock):
        rmock.delete(
            'http://baseurl/g-cloud/services/12345',
            status_code=404)

        assert search_client.delete(index='g-cloud', service_id="12345") is None

    def test_should_not_call_search_api_if_es_disabled(
            self, search_client, rmock):
        search_client._enabled = False
        rmock.put(
            'http://baseurl/g-cloud/services/12345',
            json={'message': 'acknowledged'},
            status_code=200)
        result = search_client.index(
            index_name='g-cloud',
            object_id="12345",
            serialized_object={'serialized': 'service'},
            doc_type='services',
        )
        assert result is None
        assert not rmock.called

    def test_should_raise_error_on_failure(
            self, search_client, rmock):
        with pytest.raises(APIError):
            rmock.put(
                'http://baseurl/g-cloud/services/12345',
                json={'error': 'some error'},
                status_code=400)
            search_client.index(
                index_name='g-cloud',
                object_id="12345",
                serialized_object={'serialized': 'service'},
                doc_type='services',
            )

    @pytest.mark.parametrize(
        'index, doc_type',
        (
            ('briefs-digital-outcomes-and-speciaists', 'briefs'),
            ('g-cloud-9', 'services')
        )
    )
    def test_search(self, search_client, rmock, index, doc_type):
        expected_response = {'documents': "myresponse"}
        rmock.get(
            'http://baseurl/{}/{}/search?q=foo&'
            'filter_something=a&filter_something=b'.format(index, doc_type),
            json=expected_response,
            status_code=200)
        result = search_client.search(
            index=index,
            doc_type=doc_type,
            q='foo',
            something=['a', 'b'])
        assert result == expected_response

    @pytest.mark.parametrize(
        'index, doc_type', (
            ('briefs-digital-outcomes-and-specialists', 'briefs'),
            ('g-cloud', 'services')
        )
    )
    def test_aggregate(self, search_client, rmock, index, doc_type):
        expected_response = {'aggregations': "myresponse"}
        rmock.get(
            'http://baseurl/{}/{}/aggregations?q=foo&aggregations=serviceCategories&'
            'filter_minimumContractPeriod=a&'
            'filter_something=a&filter_something=b'.format(index, doc_type),
            json=expected_response,
            status_code=200)
        result = search_client.aggregate(
            index=index,
            doc_type=doc_type,
            q='foo',
            minimumContractPeriod=['a'],
            aggregations=['serviceCategories'],
            something=['a', 'b'])
        assert result == expected_response

    @pytest.mark.parametrize(
        'index, doc_type', (
            ('briefs-digital-outcomes-and-specialists', 'briefs'),
            ('g-cloud', 'services')
        )
    )
    def test_search_with_blank_query(self, search_client, rmock, index, doc_type):
        rmock.get(
            'http://baseurl/{}/{}/search'.format(index, doc_type),
            json={'documents': "myresponse"},
            status_code=200)
        result = search_client.search(index, doc_type)
        assert result == {'documents': "myresponse"}
        assert rmock.last_request.query == ''

    @pytest.mark.parametrize(
        'index, doc_type', (
            ('briefs-digital-outcomes-and-specialists', 'briefs'),
            ('g-cloud', 'services')
        )
    )
    def test_search_with_pagination(self, search_client, rmock, doc_type, index):
        rmock.get(
            'http://baseurl/{}/{}/search?page=10'.format(index, doc_type),
            json={'documents': "myresponse"},
            status_code=200)
        result = search_client.search(index, doc_type, page=10)
        assert result == {'documents': "myresponse"}
        assert rmock.last_request.query == 'page=10'

    @pytest.mark.parametrize(
        'index, doc_type', (
            ('briefs-digital-outcomes-and-specialists', 'briefs'),
            ('g-cloud', 'services')
        )
    )
    def test_search_services_id_only(self, search_client, rmock, doc_type, index):
        rmock.get(
            'http://baseurl/{}/{}/search?idOnly=True'.format(index, doc_type),
            json={'documents': "myresponse"},
            status_code=200)
        result = search_client.search(index, doc_type, id_only=True)
        assert result == {'documents': "myresponse"}

    @staticmethod
    def load_example_listing(name):
        file_path = os.path.join("example_listings", "{}.json".format(name))
        with open(file_path) as f:
            return json.load(f)

    @pytest.mark.parametrize(
        'search_api_url, expected_frontend_params',
        (
            ('http://localhost/search', []),
            ('http://localhost/search?lot=cloud-hosting', [('lot', 'cloud-hosting')]),
            ('http://localhost/search?filter_phoneSupport=true', [('phoneSupport', 'true')]),
            (
                'http://localhost/search?filter_governmentSecurityClearances=dv%2Csc',
                [('governmentSecurityClearances', 'dv,sc')]
            ),
            (
                'http://localhost/search?filter_userAuthentication=two_factor&filter_userAuthentication=pka',
                [('userAuthentication', 'two_factor'), ('userAuthentication', 'pka')]
            )
        ))
    def test_get_frontend_params_from_search_api_url(self, search_client, rmock, search_api_url,
                                                     expected_frontend_params):
        assert search_client.get_frontend_params_from_search_api_url(search_api_url) == expected_frontend_params

    @pytest.mark.parametrize('path, index',
                             (
                                 ('search', 'g-cloud-9'),
                                 ('search', 'g-cloud-8'),
                                 ('aggregations', 'g-cloud-9'),
                                 ('aggregations', 'g-cloud-8'),
                             ))
    def test_get_url(self, search_client, path, index):
        expected_url = 'http://baseurl/{}/services/{}'.format(index, path)
        assert search_client.get_url(path=path, index=index, q=None) == expected_url

    def test_get_search_url(self, search_client):
        assert search_client.get_search_url('g-cloud-9') == 'http://baseurl/g-cloud-9/services/search'

    @pytest.mark.parametrize(
        'search_api_url, expected_index',
        (
            ('http://localhost/g-cloud-8/services/search', 'g-cloud-8'),
            ('http://localhost/g-cloud-9/services/search', 'g-cloud-9'),
            ('http://localhost/briefs-digital-outcomes-and-specialists-2/briefs/search', 'briefs-digital-outcomes-and-specialists-2'),  # NOQA
            ('https://search-api.preview.marketplace.team/g-cloud-9/services/search', 'g-cloud-9'),
            ('https://search-api.preview.marketplace.team/g-cloud-8/services/search', 'g-cloud-8'),
            ('https://search-api.preview.marketplace.team/briefs-digital-outcomes-and-specialists-2/briefs/search', 'briefs-digital-outcomes-and-specialists-2'),  # NOQA
            ('https://some.broken.url.com/that/does/not/match', None)
        )
    )
    def test_get_index_from_search_api_url(self, search_client, search_api_url, expected_index):
        assert search_client.get_index_from_search_api_url(search_api_url) == expected_index

    def test_search_service_from_url(self, search_client, rmock):
        rmock.get(
            'http://baseurl/g-cloud/services/search?lot=cloud-hosting&page=1',
            json={'services': "myresponse"},
            status_code=200)
        result = search_client.search_services_from_url(
            search_api_url='https://baseurl/g-cloud/services/search?lot=cloud-hosting',
            page=1
        )
        assert result == {'services': "myresponse"}

    def test_search_service_from_url_id_only(self, search_client, rmock):
        rmock.get(
            'http://baseurl/g-cloud/services/search?lot=cloud-hosting&page=1&idOnly=True',
            json={'services': "myresponse"},
            status_code=200)
        result = search_client.search_services_from_url(
            search_api_url='https://baseurl/g-cloud/services/search?lot=cloud-hosting',
            id_only=True,
            page=1
        )
        assert result == {'services': "myresponse"}


class TestSearchAPIClientIterMethods(object):
    def _test_find_iter(self, search_client, rmock, method_name, model_name, url_path, **kwargs):
        rmock.get(
            'http://baseurl/{}'.format(url_path),
            json={
                'links': {'next': 'http://baseurl/{}?page=2'.format(url_path)},
                model_name: [{'id': 1}, {'id': 2}]
            },
            status_code=200)
        rmock.get(
            'http://baseurl/{}?page=2'.format(url_path),
            json={
                'links': {'prev': 'http://baseurl/{}'.format(url_path)},
                model_name: [{'id': 3}]
            },
            status_code=200)

        result = getattr(search_client, method_name)(kwargs['search_url'], kwargs['id_only'])
        results = list(result)

        assert len(results) == 3
        assert results[0]['id'] == 1
        assert results[1]['id'] == 2
        assert results[2]['id'] == 3

    def test_search_services_from_url_iter_with_services_in_response_key(self, search_client, rmock):
        self._test_find_iter(
            search_client, rmock,
            method_name='search_services_from_url_iter',
            model_name='services',
            url_path='g-cloud/services/search?idOnly=True',
            search_url='http://baseurl/g-cloud/services/search',
            id_only=True)

    def test_search_services_from_url_iter_with_documents_in_response_key(self, search_client, rmock):
        self._test_find_iter(
            search_client, rmock,
            method_name='search_services_from_url_iter',
            model_name='documents',
            url_path='g-cloud/services/search?idOnly=True',
            search_url='http://baseurl/g-cloud/services/search',
            id_only=True)

    def test_search_services_from_url_iter_with_bad_response_key(self, search_client, rmock):
        with pytest.raises(AssertionError):
            self._test_find_iter(
                search_client, rmock,
                method_name='search_services_from_url_iter',
                model_name='i-am-naughty',
                url_path='g-cloud/services/search?idOnly=True',
                search_url='http://baseurl/g-cloud/services/search',
                id_only=True)
