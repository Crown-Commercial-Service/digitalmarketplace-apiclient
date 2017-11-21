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


@pytest.fixture
def service():
    """A stripped down G6-IaaS service"""
    return {
        "id": "1234567890123456",
        "supplierId": 1,
        "lot": "IaaS",
        "title": "My Iaas Service",
        "lastUpdated": "2014-12-23T14:46:17Z",
        "lastUpdatedByEmail": "supplier@digital.cabinet-office.gov.uk",
        "lastCompleted": "2014-12-23T14:46:22Z",
        "lastCompletedByEmail": "supplier@digital.cabinet-office.gov.uk",
        "serviceTypes": [
            "Compute",
            "Storage"
        ],
        "serviceName": "My Iaas Service",
        "serviceSummary": "IaaS Service Summary",
        "serviceBenefits": [
            "Free lollipop to every 10th customer",
            "It's just lovely"
        ],
        "serviceFeatures": [
            "[To be completed]",
            "This is my second \"feture\""
        ],
        "minimumContractPeriod": "Month",
        "terminationCost": True,
        "priceInterval": "",
        "trialOption": True,
        "priceUnit": "Person",
        "educationPricing": True,
        "vatIncluded": False,
        "priceString": "£10.0067 per person",
        "priceMin": 10.0067,
        "freeOption": False,
        "openStandardsSupported": True,
        "supportForThirdParties": False,
        "supportResponseTime": "3 weeks.",
        "incidentEscalation": True,
        "serviceOffboarding": True,
        "serviceOnboarding": False,
        "analyticsAvailable": False,
        "persistentStorage": True,
        "elasticCloud": True,
        "guaranteedResources": False,
        "selfServiceProvisioning": False,
        "openSource": False,
        "apiType": "SOAP, Rest | JSON",
        "apiAccess": True,
        "networksConnected": [
            "Public Services Network (PSN)",
            "Government Secure intranet (GSi)"
        ],
        "offlineWorking": True,
        "dataExtractionRemoval": False,
        "dataBackupRecovery": True,
        "datacentreTier": "TIA-942 Tier 3",
        "datacentresSpecifyLocation": True,
        "datacentresEUCode": False,
    }


@pytest.fixture
def brief():
    """A stripped down DOS2 brief"""
    return {
        'applicationsClosedAt': '2017-12-04T23:59:59.000000Z',
        'clarificationQuestions': [],
        'clarificationQuestionsAreClosed': False,
        'clarificationQuestionsClosedAt': '2017-11-27T23:59:59.000000Z',
        'clarificationQuestionsPublishedBy': '2017-12-01T23:59:59.000000Z',
        'contractLength': '3 weeks',
        'createdAt': '2017-11-20T17:11:44.827229Z',
        'culturalFitCriteria': ['CULTURAL', 'FIT'],
        'culturalWeighting': 5,
        'essentialRequirements': ['MS Paint', 'GIMP'],
        'evaluationType': ['Reference', 'Interview'],
        'existingTeam': 'Nice people.',
        'frameworkFramework': 'digital-outcomes-and-specialists',
        'frameworkName': 'Digital Outcomes and Specialists 2',
        'frameworkSlug': 'digital-outcomes-and-specialists-2',
        'frameworkStatus': 'live',
        'id': 1,
        'isACopy': False,
        'links': {
            'framework': 'http://127.0.0.1:5000/frameworks/digital-outcomes-and-specialists-2',
            'self': 'http://127.0.0.1:5000/briefs/1'
        },
        'location': 'Wales',
        'lot': 'digital-specialists',
        'lotName': 'Digital specialists',
        'lotSlug': 'digital-specialists',
        'niceToHaveRequirements': ['LISP'],
        'numberOfSuppliers': 3,
        'organisation': 'Org.org',
        'priceWeighting': 85,
        'publishedAt': '2017-11-20T17:11:44.812563Z',
        'requirementsLength': '2 weeks',
        'securityClearance': 'Developed vetting required.',
        'specialistRole': 'developer',
        'specialistWork': 'All the things',
        'startDate': '31-12-2016',
        'status': 'live',
        'summary': 'Doing some stuff to help out.',
        'technicalWeighting': 10,
        'updatedAt': '2017-11-20T17:11:44.827236Z',
        'users': [{
            'active': True,
            'emailAddress': 'test+1@digital.gov.uk',
            'id': 1,
            'name': 'my name',
            'phoneNumber': None,
            'role': 'buyer'
        }],
        'workingArrangements': 'Just get the work done.',
        'workplaceAddress': 'Aviation House'
    }


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
            self, search_client, rmock, brief):
        rmock.put(
            'http://baseurl/briefs-digital-outcomes-and-specialists-2/briefs/12345',
            json={'message': 'acknowledged'},
            status_code=200)
        result = search_client.index(
            'briefs-digital-outcomes-and-specialists-2',
            "12345",
            brief,
            object_type='briefs',
        )
        assert result == {'message': 'acknowledged'}

    def test_post_to_index_without_type_defaults_to_services(
            self, search_client, rmock, brief):
        rmock.put(
            'http://baseurl/g-cloud-9/services/12345',
            json={'message': 'acknowledged'},
            status_code=200)
        result = search_client.index(
            'g-cloud-9',
            "12345",
            brief
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
            self, search_client, rmock, service):
        search_client.enabled = False
        rmock.put(
            'http://baseurl/g-cloud/services/12345',
            json={'message': 'acknowledged'},
            status_code=200)
        result = search_client.index(
            index_name='g-cloud',
            object_type='services',
            object_id="12345",
            serialized_object=service
        )
        assert result is None
        assert not rmock.called

    def test_should_raise_error_on_failure(
            self, search_client, rmock, service):
        with pytest.raises(APIError):
            rmock.put(
                'http://baseurl/g-cloud/services/12345',
                json={'error': 'some error'},
                status_code=400)
            search_client.index(
                index_name='g-cloud',
                object_type='services',
                object_id="12345",
                serialized_object=service
            )

    def test_search_services(self, search_client, rmock):
        expected_response = {'services': "myresponse"}
        rmock.get(
            'http://baseurl/g-cloud/services/search?q=foo&'
            'filter_minimumContractPeriod=a&'
            'filter_something=a&filter_something=b',
            json=expected_response,
            status_code=200)
        result = search_client.search_services(
            index='g-cloud',
            q='foo',
            minimumContractPeriod=['a'],
            something=['a', 'b'])
        assert result == expected_response

    def test_aggregate_services(self, search_client, rmock):
        expected_response = {'aggregations': "myresponse"}
        rmock.get(
            'http://baseurl/g-cloud/services/aggregations?q=foo&aggregations=serviceCategories&'
            'filter_minimumContractPeriod=a&'
            'filter_something=a&filter_something=b',
            json=expected_response,
            status_code=200)
        result = search_client.aggregate_services(
            index='g-cloud',
            q='foo',
            minimumContractPeriod=['a'],
            aggregations=['serviceCategories'],
            something=['a', 'b'])
        assert result == expected_response

    def test_search_services_with_blank_query(self, search_client, rmock):
        rmock.get(
            'http://baseurl/g-cloud/services/search',
            json={'services': "myresponse"},
            status_code=200)
        result = search_client.search_services(index='g-cloud')
        assert result == {'services': "myresponse"}
        assert rmock.last_request.query == ''

    def test_search_services_with_pagination(self, search_client, rmock):
        rmock.get(
            'http://baseurl/g-cloud/services/search?page=10',
            json={'services': "myresponse"},
            status_code=200)
        result = search_client.search_services(index='g-cloud', page=10)
        assert result == {'services': "myresponse"}
        assert rmock.last_request.query == 'page=10'

    def test_search_services_id_only(self, search_client, rmock):
        rmock.get(
            'http://baseurl/g-cloud/services/search?idOnly=True',
            json={'services': "myresponse"},
            status_code=200)
        result = search_client.search_services(index='g-cloud', id_only=True)
        assert result == {'services': "myresponse"}

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

        result = getattr(search_client, method_name)(**kwargs)
        results = list(result)

        assert len(results) == 3
        assert results[0]['id'] == 1
        assert results[1]['id'] == 2
        assert results[2]['id'] == 3

    def test_search_services_from_url_iter(self, search_client, rmock):
        self._test_find_iter(
            search_client, rmock,
            method_name='search_services_from_url_iter',
            model_name='services',
            url_path='g-cloud/services/search',
            search_api_url='http://baseurl/g-cloud/services/search')
