# -*- coding: utf-8 -*-
import os

from flask import json, request
import requests
import requests_mock
import pytest
import mock

from dmapiclient.base import BaseAPIClient
from dmapiclient import SearchAPIClient, DataAPIClient
from dmapiclient import APIError, HTTPError, InvalidResponse
from dmapiclient.errors import REQUEST_ERROR_STATUS_CODE
from dmapiclient.errors import REQUEST_ERROR_MESSAGE
from dmapiclient.audit import AuditTypes
from dmapiclient.exceptions import ImproperlyConfigured


@pytest.yield_fixture
def rmock():
    with requests_mock.mock() as rmock:
        yield rmock


@pytest.yield_fixture
def raw_rmock():
    with mock.patch('dmapiclient.base.requests.request') as rmock:
        yield rmock


@pytest.fixture
def base_client():
    return BaseAPIClient('http://baseurl', 'auth-token', True)


@pytest.fixture
def search_client():
    return SearchAPIClient('http://baseurl', 'auth-token', True)


@pytest.fixture
def data_client():
    return DataAPIClient('http://baseurl', 'auth-token', True)


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


class TestBaseApiClient(object):
    def test_connection_error_raises_api_error(self, base_client, raw_rmock):
        raw_rmock.side_effect = requests.exceptions.ConnectionError(
            None
        )
        with pytest.raises(HTTPError) as e:
            base_client._request("GET", '/')

        assert e.value.message == REQUEST_ERROR_MESSAGE
        assert e.value.status_code == REQUEST_ERROR_STATUS_CODE

    def test_http_error_raises_api_error(self, base_client, rmock):
        rmock.request(
            "GET",
            "http://baseurl/",
            text="Internal Error",
            status_code=500)

        with pytest.raises(HTTPError) as e:
            base_client._request("GET", '/')

        assert e.value.message == REQUEST_ERROR_MESSAGE
        assert e.value.status_code == 500

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
        assert app.search_api_client is search_client

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

        result = search_client.create_index('new-index')

        assert rmock.called
        assert result['status'] == "ok"
        assert rmock.last_request.json() == {
            "type": "index"
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

    def test_post_to_index_with_type_and_service_id(
            self, search_client, rmock, service):
        rmock.put(
            'http://baseurl/g-cloud/services/12345',
            json={'message': 'acknowledged'},
            status_code=200)
        result = search_client.index("12345", service)
        assert result == {'message': 'acknowledged'}

    def test_post_to_given_index(
            self, search_client, rmock, service):
        rmock.put(
            'http://baseurl/new-index/services/12345',
            json={'message': 'acknowledged'},
            status_code=200)
        result = search_client.index("12345", service, index='new-index')
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
        result = search_client.delete("12345")
        assert result['services']['found'] is True

    def test_delete_from_given_index(
            self, search_client, rmock, service):
        rmock.delete(
            'http://baseurl/new-index/services/12345',
            json={'message': 'acknowledged'},
            status_code=200)
        result = search_client.delete("12345", index='new-index')
        assert result == {'message': 'acknowledged'}

    def test_should_not_call_search_api_is_es_disabled(
            self, search_client, rmock, service):
        search_client.enabled = False
        rmock.put(
            'http://baseurl/g-cloud/services/12345',
            json={'message': 'acknowledged'},
            status_code=200)
        result = search_client.index("12345", service)
        assert result is None
        assert not rmock.called

    def test_should_raise_error_on_failure(
            self, search_client, rmock, service):
        with pytest.raises(APIError):
            rmock.put(
                'http://baseurl/g-cloud/services/12345',
                json={'error': 'some error'},
                status_code=400)
            search_client.index("12345", service)

    def test_search_services(self, search_client, rmock):
        rmock.get(
            'http://baseurl/g-cloud/services/search?q=foo&'
            'filter_minimumContractPeriod=a&'
            'filter_something=a&filter_something=b',
            json={'services': "myresponse"},
            status_code=200)
        result = search_client.search_services(
            q='foo',
            minimumContractPeriod=['a'],
            something=['a', 'b'])
        assert result == {'services': "myresponse"}

    def test_search_given_index(self, search_client, rmock):
        rmock.get(
            'http://baseurl/new-index/services/search?q=foo&filter_minimumContractPeriod=a',
            json={'services': "myresponse"},
            status_code=200
        )

        result = search_client.search_services(
            q='foo',
            minimumContractPeriod=['a'],
            index='new-index',
        )

        assert result == {'services': "myresponse"}

    def test_search_services_with_blank_query(self, search_client, rmock):
        rmock.get(
            'http://baseurl/g-cloud/services/search',
            json={'services': "myresponse"},
            status_code=200)
        result = search_client.search_services()
        assert result == {'services': "myresponse"}
        assert rmock.last_request.query == ''

    def test_search_services_with_pagination(self, search_client, rmock):
        rmock.get(
            'http://baseurl/g-cloud/services/search?page=10',
            json={'services': "myresponse"},
            status_code=200)
        result = search_client.search_services(page=10)
        assert result == {'services': "myresponse"}
        assert rmock.last_request.query == 'page=10'

    @staticmethod
    def load_example_listing(name):
        file_path = os.path.join("example_listings", "{}.json".format(name))
        with open(file_path) as f:
            return json.load(f)


class TestDataApiClient(object):
    def test_request_id_is_added_if_available(self, data_client, rmock, app):
        with app.test_request_context('/'):
            app.config['DM_REQUEST_ID_HEADER'] = 'DM-Request-Id'
            request.request_id = 'generated'
            rmock.get("http://baseurl/_status", json={"status": "ok"}, status_code=200)

            data_client.get_status()

            assert rmock.last_request.headers["DM-Request-Id"] == "generated"

    def test_request_id_is_not_added_if_logging_is_not_loaded(self, data_client, rmock, app):
        headers = {'DM-Request-Id': 'generated'}
        with app.test_request_context('/', headers=headers):
            rmock.get(
                "http://baseurl/_status",
                json={"status": "ok"},
                status_code=200)

            data_client.get_status()

            assert "DM-Request-Id" not in rmock.last_request.headers

    def test_init_app_sets_attributes(self, data_client):
        app = mock.Mock()
        app.config = {
            "DM_DATA_API_URL": "http://example",
            "DM_DATA_API_AUTH_TOKEN": "example-token",
            }
        data_client.init_app(app)

        assert data_client.base_url == "http://example"
        assert data_client.auth_token == "example-token"
        assert app.data_api_client is data_client

    def test_get_status(self, data_client, rmock):
        rmock.get(
            "http://baseurl/_status",
            json={"status": "ok"},
            status_code=200)

        result = data_client.get_status()

        assert result['status'] == "ok"
        assert rmock.called

    def test_get_archived_service(self, data_client, rmock):
        rmock.get(
            "http://baseurl/archived-services/123",
            json={"services": "result"},
            status_code=200)

        result = data_client.get_archived_service(123)

        assert result == {"services": "result"}
        assert rmock.called

    def test_get_service(self, data_client, rmock):
        rmock.get(
            "http://baseurl/services/123",
            json={"services": "result"},
            status_code=200)

        result = data_client.get_service(123)

        assert result == {"services": "result"}
        assert rmock.called

    def test_get_service_returns_none_on_404(self, data_client, rmock):
        rmock.get(
            'http://baseurl/services/123',
            json={'services': 'result'},
            status_code=404)

        result = data_client.get_service(123)

        assert result is None

    def test_get_service_raises_on_non_404(self, data_client, rmock):
        with pytest.raises(APIError):
            rmock.get(
                'http://baseurl/services/123',
                json={'services': 'result'},
                status_code=400)

            data_client.get_service(123)

    def test_find_services(self, data_client, rmock):
        rmock.get(
            "http://baseurl/services",
            json={"services": "result"},
            status_code=200)

        result = data_client.find_services()

        assert result == {"services": "result"}
        assert rmock.called

    def test_find_services_adds_page_parameter(self, data_client, rmock):
        rmock.get(
            "http://baseurl/services?page=2",
            json={"services": "result"},
            status_code=200)

        result = data_client.find_services(page=2)

        assert result == {"services": "result"}
        assert rmock.called

    def test_find_services_adds_supplier_id_parameter(
            self, data_client, rmock):
        rmock.get(
            "http://baseurl/services?supplier_id=1",
            json={"services": "result"},
            status_code=200)

        result = data_client.find_services(supplier_id=1)

        assert result == {"services": "result"}
        assert rmock.called

    def test_import_service(self, data_client, rmock):
        rmock.put(
            "http://baseurl/services/123",
            json={"services": "result"},
            status_code=201,
        )

        result = data_client.import_service(
            123, {"foo": "bar"}, "person")

        assert result == {"services": "result"}
        assert rmock.called

    def test_update_service(self, data_client, rmock):
        rmock.post(
            "http://baseurl/services/123",
            json={"services": "result"},
            status_code=200,
        )

        result = data_client.update_service(
            123, {"foo": "bar"}, "person")

        assert result == {"services": "result"}
        assert rmock.called

    def test_update_service_status(self, data_client, rmock):
        rmock.post(
            "http://baseurl/services/123/status/published",
            json={"services": "result"},
            status_code=200,
        )

        result = data_client.update_service_status(
            123, "published", "person")

        assert result == {"services": "result"}
        assert rmock.called

    def test_find_users_by_supplier_id(self, data_client, rmock):
        rmock.get(
            "http://baseurl/users?supplier_id=1234",
            json=self.user(),
            status_code=200)
        user = data_client.find_users(1234)

        assert user == self.user()

    def test_find_users_not_possible_with_supplier_id_and_role(self, data_client, rmock):
        with pytest.raises(ValueError):
            data_client.find_users(supplier_id=123, role='buyer')

    def test_find_users_by_role(self, data_client, rmock):
        rmock.get(
            "http://baseurl/users?role=buyer",
            json=self.user(),
            status_code=200)

        user = data_client.find_users(role='buyer')

        assert user == self.user()

    def test_find_users_by_page(self, data_client, rmock):
        rmock.get(
            "http://baseurl/users?page=12",
            json=self.user(),
            status_code=200)
        user = data_client.find_users(page=12)

        assert user == self.user()

    def test_get_user_by_id(self, data_client, rmock):
        rmock.get(
            "http://baseurl/users/1234",
            json=self.user(),
            status_code=200)
        user = data_client.get_user(user_id=1234)

        assert user == self.user()

    def test_get_user_by_email_address(self, data_client, rmock):
        rmock.get(
            "http://baseurl/users?email_address=myemail",
            json=self.user(),
            status_code=200)
        user = data_client.get_user(email_address="myemail")

        assert user == self.user()

    def test_get_user_fails_if_both_email_and_id_are_provided(
            self, data_client, rmock):

        with pytest.raises(ValueError):
            data_client.get_user(user_id=123, email_address="myemail")

    def test_get_user_fails_if_neither_email_or_id_are_provided(
            self, data_client, rmock):

        with pytest.raises(ValueError):
            data_client.get_user()

    def test_get_user_returns_none_on_404(self, data_client, rmock):
        rmock.get(
            "http://baseurl/users/123",
            json={"not": "found"},
            status_code=404)

        user = data_client.get_user(user_id=123)

        assert user is None

    def test_authenticate_user_is_called_with_correct_params(
            self, data_client, rmock):
        rmock.post(
            "http://baseurl/users/auth",
            json=self.user(),
            status_code=200)

        user = data_client.authenticate_user("email_address", "password")['users']

        assert user['id'] == "id"
        assert user['email_address'] == "email_address"
        assert user['supplier']['supplier_id'] == 1234
        assert user['supplier']['name'] == "name"

    def test_authenticate_user_returns_none_on_404(
            self, data_client, rmock):
        rmock.post(
            'http://baseurl/users/auth',
            text=json.dumps({'authorization': False}),
            status_code=404)

        user = data_client.authenticate_user("email_address", "password")

        assert user is None

    def test_authenticate_user_returns_none_on_403(
            self, data_client, rmock):
        rmock.post(
            'http://baseurl/users/auth',
            text=json.dumps({'authorization': False}),
            status_code=403)

        user = data_client.authenticate_user("email_address", "password")

        assert user is None

    def test_authenticate_user_returns_none_on_400(
            self, data_client, rmock):
        rmock.post(
            'http://baseurl/users/auth',
            text=json.dumps({'authorization': False}),
            status_code=400)

        user = data_client.authenticate_user("email_address", "password")

        assert user is None

    def test_authenticate_user_returns_buyer_user(
            self, data_client, rmock):
        user_with_no_supplier = self.user()
        del user_with_no_supplier['users']['supplier']
        user_with_no_supplier['users']['role'] = 'buyer'

        rmock.post(
            'http://baseurl/users/auth',
            text=json.dumps(user_with_no_supplier),
            status_code=200)

        user = data_client.authenticate_user("email_address", "password")

        assert user == user_with_no_supplier

    def test_authenticate_user_raises_on_500(self, data_client, rmock):
        with pytest.raises(APIError):
            rmock.post(
                'http://baseurl/users/auth',
                text=json.dumps({'authorization': False}),
                status_code=500)

            data_client.authenticate_user("email_address", "password")

    def test_create_user(self, data_client, rmock):
        rmock.post(
            "http://baseurl/users",
            json={"users": "result"},
            status_code=201)

        result = data_client.create_user({"foo": "bar"})

        assert result == {"users": "result"}
        assert rmock.called

    def test_update_user_password(self, data_client, rmock):
        rmock.post(
            "http://baseurl/users/123",
            json={},
            status_code=200)
        assert data_client.update_user_password(123, "newpassword")
        assert rmock.last_request.json() == {
            "users": {
                "password": "newpassword"
            },
            "updated_by": "no logged-in user"
        }

    def test_update_user_password_by_logged_in_user(self, data_client, rmock):
        rmock.post(
            "http://baseurl/users/123",
            json={},
            status_code=200)
        assert data_client.update_user_password(123, "newpassword", "test@example.com")
        assert rmock.last_request.json() == {
            "users": {
                "password": "newpassword"
            },
            "updated_by": "test@example.com"
        }

    def test_update_user_password_returns_false_on_non_200(
            self, data_client, rmock):
        for status_code in [400, 403, 404, 500]:
            rmock.post(
                "http://baseurl/users/123",
                json={},
                status_code=status_code)
            assert not data_client.update_user_password(123, "newpassword")

    def test_update_user_returns_false_on_non_200(self, data_client, rmock):
        for status_code in [400, 403, 404, 500]:
            rmock.post(
                "http://baseurl/users/123",
                json={},
                status_code=status_code)
            with pytest.raises(HTTPError) as e:
                data_client.update_user(123)

            assert e.value.status_code == status_code

    def test_can_change_user_role(self, data_client, rmock):
        rmock.post(
            "http://baseurl/users/123",
            json={},
            status_code=200)
        data_client.update_user(123, role='supplier', updater="test@example.com")
        assert rmock.called
        assert rmock.last_request.json() == {
            "updated_by": "test@example.com",
            "users": {"role": 'supplier'}
        }

    def test_can_add_user_supplier_id(self, data_client, rmock):
        rmock.post(
            "http://baseurl/users/123",
            json={},
            status_code=200)
        data_client.update_user(123, supplier_id=123, updater="test@example.com")
        assert rmock.called
        assert rmock.last_request.json() == {
            "updated_by": "test@example.com",
            "users": {"supplierId": 123}
        }

    def test_make_user_a_supplier(self, data_client, rmock):
        rmock.post(
            "http://baseurl/users/123",
            json={},
            status_code=200)
        data_client.update_user(123, supplier_id=123, role='supplier', updater="test@example.com")
        assert rmock.called
        assert rmock.last_request.json() == {
            "updated_by": "test@example.com",
            "users": {
                "supplierId": 123,
                "role": "supplier"
            }
        }

    def test_can_unlock_user(self, data_client, rmock):
        rmock.post(
            "http://baseurl/users/123",
            json={},
            status_code=200)
        data_client.update_user(123, locked=False, updater="test@example.com")
        assert rmock.called
        assert rmock.last_request.json() == {
            "updated_by": "test@example.com",
            "users": {"locked": False}
        }

    def test_can_activate_user(self, data_client, rmock):
        rmock.post(
            "http://baseurl/users/123",
            json={},
            status_code=200)
        data_client.update_user(123, active=True, updater="test@example.com")
        assert rmock.called
        assert rmock.last_request.json() == {
            "updated_by": "test@example.com",
            "users": {"active": True}
        }

    def test_can_deactivate_user(self, data_client, rmock):
        rmock.post(
            "http://baseurl/users/123",
            json={},
            status_code=200)
        data_client.update_user(123, active=False, updater="test@example.com")
        assert rmock.called
        assert rmock.last_request.json() == {
            "updated_by": "test@example.com",
            "users": {"active": False}
        }

    def test_can_export_users(self, data_client, rmock):
        rmock.get(
            "http://baseurl/users/export/g-cloud-7",
            json={"users": "result"},
            status_code=200)
        result = data_client.export_users('g-cloud-7')
        assert rmock.called
        assert result == {"users": "result"}

    def test_is_email_address_with_valid_buyer_domain_true(self, data_client, rmock):
        rmock.get(
            "http://baseurl/users/check-buyer-email?email_address=kev%40gov.uk",
            json={"valid": True},
            status_code=200)
        result = data_client.is_email_address_with_valid_buyer_domain('kev@gov.uk')
        assert rmock.called
        assert result is True

    def test_is_email_address_with_valid_buyer_domain_false(self, data_client, rmock):
        rmock.get(
            "http://baseurl/users/check-buyer-email?email_address=kev%40ymail.com",
            json={"valid": False},
            status_code=200)
        result = data_client.is_email_address_with_valid_buyer_domain('kev@ymail.com')
        assert rmock.called
        assert result is False

    @staticmethod
    def user():
        return {'users': {
            'id': 'id',
            'email_address': 'email_address',
            'name': 'name',
            'role': 'supplier',
            'active': 'active',
            'locked': False,
            'created_at': "2015-05-05T05:05:05",
            'updated_at': "2015-05-05T05:05:05",
            'password_changed_at': "2015-05-05T05:05:05",
            'supplier': {
                'supplier_id': 1234,
                'name': 'name'
            }
        }}

    def test_find_suppliers_with_no_prefix(self, data_client, rmock):
        rmock.get(
            "http://baseurl/suppliers",
            json={"services": "result"},
            status_code=200)

        result = data_client.find_suppliers()

        assert result == {"services": "result"}
        assert rmock.called

    def test_find_suppliers_with_prefix(self, data_client, rmock):
        rmock.get(
            "http://baseurl/suppliers?prefix=a",
            json={"services": "result"},
            status_code=200)

        result = data_client.find_suppliers(prefix='a')

        assert result == {"services": "result"}
        assert rmock.called

    def test_find_suppliers_with_framework(self, data_client, rmock):
        rmock.get(
            "http://baseurl/suppliers?framework=gcloud",
            json={"services": "result"},
            status_code=200)

        result = data_client.find_suppliers(framework='gcloud')

        assert result == {"services": "result"}
        assert rmock.called

    def test_find_suppliers_with_duns_number(self, data_client, rmock):
        rmock.get(
            "http://baseurl/suppliers?duns_number=1234",
            json={"services": "result"},
            status_code=200)

        result = data_client.find_suppliers(duns_number='1234')

        assert result == {"services": "result"}
        assert rmock.called

    def test_find_supplier_adds_page_parameter(self, data_client, rmock):
        rmock.get(
            "http://baseurl/suppliers?page=2",
            json={"suppliers": "result"},
            status_code=200)

        result = data_client.find_suppliers(page=2)

        assert result == {"suppliers": "result"}
        assert rmock.called

    def test_find_services_by_supplier(self, data_client, rmock):
        rmock.get(
            "http://baseurl/services?supplier_id=123",
            json={"services": "result"},
            status_code=200)

        result = data_client.find_services(supplier_id=123)

        assert result == {"services": "result"}
        assert rmock.called

    def test_get_supplier_by_id(self, data_client, rmock):
        rmock.get(
            "http://baseurl/suppliers/123",
            json={"services": "result"},
            status_code=200)

        result = data_client.get_supplier(123)

        assert result == {"services": "result"}
        assert rmock.called

    def test_get_supplier_by_id_should_return_404(self, data_client, rmock):
        rmock.get(
            "http://baseurl/suppliers/123",
            status_code=404)

        try:
            data_client.get_supplier(123)
        except HTTPError:
            assert rmock.called

    def test_import_supplier(self, data_client, rmock):
        rmock.put(
            "http://baseurl/suppliers/123",
            json={"suppliers": "result"},
            status_code=201,
        )

        result = data_client.import_supplier(123, {"foo": "bar"})

        assert result == {"suppliers": "result"}
        assert rmock.called

    def test_create_supplier(self, data_client, rmock):
        rmock.post(
            "http://baseurl/suppliers",
            json={"suppliers": "result"},
            status_code=201,
        )

        result = data_client.create_supplier({"foo": "bar"})

        assert result == {"suppliers": "result"}
        assert rmock.called

    def test_update_supplier(self, data_client, rmock):
        rmock.post(
            "http://baseurl/suppliers/123",
            json={"suppliers": "result"},
            status_code=201,
        )

        result = data_client.update_supplier(123, {"foo": "bar"}, 'supplier')

        assert result == {"suppliers": "result"}
        assert rmock.called
        assert rmock.request_history[0].json() == {
            'suppliers': {'foo': 'bar'}, 'updated_by': 'supplier'
        }

    def test_update_contact_information(self, data_client, rmock):
        rmock.post(
            "http://baseurl/suppliers/123/contact-information/2",
            json={"suppliers": "result"},
            status_code=201,
        )

        result = data_client.update_contact_information(
            123, 2, {"foo": "bar"}, 'supplier'
        )

        assert result == {"suppliers": "result"}
        assert rmock.called
        assert rmock.request_history[0].json() == {
            'contactInformation': {'foo': 'bar'}, 'updated_by': 'supplier'
        }

    def test_get_framework_interest(self, data_client, rmock):
        rmock.get(
            "http://baseurl/suppliers/123/frameworks/interest",
            json={"frameworks": ['g-cloud-15', 'dos-23']},
            status_code=200)

        result = data_client.get_framework_interest(123)

        assert result == {"frameworks": ['g-cloud-15', 'dos-23']}
        assert rmock.called

    def test_register_framework_interest(self, data_client, rmock):
        rmock.put(
            "http://baseurl/suppliers/123/frameworks/g-cloud-15",
            json={"frameworkInterest": {"supplierId": 123, "frameworkId": 19}},
            status_code=200)

        result = data_client.register_framework_interest(123, 'g-cloud-15', "g-15-user")

        assert result == {"frameworkInterest": {"supplierId": 123, "frameworkId": 19}}
        assert rmock.called
        assert rmock.request_history[0].json() == {'updated_by': 'g-15-user'}

    def test_get_supplier_declaration(self, data_client, rmock):
        rmock.get(
            "http://baseurl/suppliers/123/frameworks/g-cloud-7",
            json={"frameworkInterest": {"declaration": {"question": "answer"}}},
            status_code=200)

        result = data_client.get_supplier_declaration(123, 'g-cloud-7')

        assert result == {'declaration': {'question': 'answer'}}
        assert rmock.called

    def test_set_supplier_declaration(self, data_client, rmock):
        rmock.put(
            "http://baseurl/suppliers/123/frameworks/g-cloud-7/declaration",
            json={"declaration": {"question": "answer"}},
            status_code=200)

        result = data_client.set_supplier_declaration(123, 'g-cloud-7', {"question": "answer"}, "user")

        assert result == {'declaration': {'question': 'answer'}}
        assert rmock.called
        assert rmock.request_history[0].json() == {
            'updated_by': 'user',
            'declaration': {'question': 'answer'}}

    def test_get_supplier_frameworks(self, data_client, rmock):
        rmock.get(
            "http://baseurl/suppliers/123/frameworks",
            json={"frameworkInterest": [{"declaration": {"status": "started"}}]},
            status_code=200)

        result = data_client.get_supplier_frameworks(123)

        assert result == {"frameworkInterest": [{"declaration": {"status": "started"}}]}
        assert rmock.called

    def test_get_supplier_framework_info(self, data_client, rmock):
        rmock.get(
            "http://baseurl/suppliers/123/frameworks/g-cloud-7",
            json={"frameworkInterest": {"supplierId": 123, "frameworkId": 2, "onFramework": False}},
            status_code=200)
        result = data_client.get_supplier_framework_info(123, 'g-cloud-7')
        assert result == {"frameworkInterest": {"supplierId": 123, "frameworkId": 2, "onFramework": False}}
        assert rmock.called

    def test_set_framework_result(self, data_client, rmock):
        rmock.post(
            "http://baseurl/suppliers/123/frameworks/g-cloud-7",
            json={"frameworkInterest": {"onFramework": True}},
            status_code=200)

        result = data_client.set_framework_result(123, 'g-cloud-7', True, "user")
        assert result == {"frameworkInterest": {"onFramework": True}}
        assert rmock.called
        assert rmock.request_history[0].json() == {
            'frameworkInterest': {'onFramework': True},
            'updated_by': 'user'
        }

    def test_register_framework_agreement_returned_with_uploader_user_id(self, data_client, rmock):
        rmock.post(
            "http://baseurl/suppliers/123/frameworks/g-cloud-8",
            json={
                'frameworkInterest': {
                    'agreementReturned': True,
                    'agreementDetails': {'uploaderUserId': 10},
                },
            },
            status_code=200)

        result = data_client.register_framework_agreement_returned(
            123, 'g-cloud-8', "user", 10
        )
        assert result == {
            'frameworkInterest': {
                'agreementReturned': True,
                'agreementDetails': {'uploaderUserId': 10},
            },
        }
        assert rmock.called
        assert rmock.request_history[0].json() == {
            'frameworkInterest': {
                'agreementReturned': True,
                'agreementDetails': {'uploaderUserId': 10},
            },
            'updated_by': 'user',
        }

    def test_register_framework_agreement_returned_without_uploader_user_id(self, data_client, rmock):
        rmock.post(
            "http://baseurl/suppliers/123/frameworks/g-cloud-7",
            json={
                'frameworkInterest': {
                    'agreementReturned': True,
                },
            },
            status_code=200)

        result = data_client.register_framework_agreement_returned(123, 'g-cloud-7', "user")
        assert result == {
            'frameworkInterest': {
                'agreementReturned': True,
            },
        }
        assert rmock.called
        assert rmock.request_history[0].json() == {
            'frameworkInterest': {
                'agreementReturned': True,
            },
            'updated_by': 'user',
        }

    def test_unset_framework_agreement_returned(self, data_client, rmock):
        rmock.post(
            "http://baseurl/suppliers/123/frameworks/g-cloud-7",
            json={"frameworkInterest": {"agreementReturned": False}},
            status_code=200)

        result = data_client.unset_framework_agreement_returned(123, 'g-cloud-7', "user")
        assert result == {"frameworkInterest": {"agreementReturned": False}}
        assert rmock.called
        assert rmock.request_history[0].json() == {
            'frameworkInterest': {'agreementReturned': False},
            'updated_by': 'user'
        }

    def test_update_supplier_framework_agreement_details(self, data_client, rmock):
        rmock.post(
            "http://baseurl/suppliers/123/frameworks/g-cloud-8",
            json={
                'frameworkInterest': {
                    'agreementDetails': {'signerName': 'name'},
                },
            },
            status_code=200)

        result = data_client.update_supplier_framework_agreement_details(
            123, 'g-cloud-8', {'signerName': 'name'}, "user"
        )
        assert result == {
            'frameworkInterest': {
                'agreementDetails': {'signerName': 'name'}
            },
        }
        assert rmock.called
        assert rmock.request_history[0].json() == {
            'frameworkInterest': {
                'agreementDetails': {'signerName': 'name'}
            },
            'updated_by': 'user',
        }

    def test_register_framework_agreement_countersigned(self, data_client, rmock):
        rmock.post(
            "http://baseurl/suppliers/123/frameworks/g-cloud-7",
            json={"frameworkInterest": {"countersigned": True}},
            status_code=200)

        result = data_client.register_framework_agreement_countersigned(123, 'g-cloud-7', "user")
        assert result == {"frameworkInterest": {"countersigned": True}}
        assert rmock.called
        assert rmock.request_history[0].json() == {
            'frameworkInterest': {'countersigned': True},
            'updated_by': 'user'
        }

    def test_agree_framework_variation(self, data_client, rmock):
        dummy_response_body = {
            "agreedVariations": {
                "agreedAt": "2016-01-23T12:34:56.000000Z",
                "agreedUserId": 314,
                "agreedUserEmail": "example@digital.gov.uk",
                "agreedUserName": "Paddy Dignam",
            },
        }
        rmock.put(
            "http://baseurl/suppliers/321/frameworks/g-cloud-99/variation/banana-split",
            json=dummy_response_body,
            status_code=200)

        result = data_client.agree_framework_variation(321, 'g-cloud-99', "banana-split", 314, "someuser")
        assert result == dummy_response_body
        assert rmock.called
        assert [rh.json() for rh in rmock.request_history] == [{
            "agreedVariations": {
                "agreedUserId": 314,
            },
            "updated_by": "someuser",
        }]

    def test_find_framework_suppliers(self, data_client, rmock):
        rmock.get(
            'http://baseurl/frameworks/g-cloud-7/suppliers',
            json={'supplierFrameworks': [{"agreementReturned": False}, {"agreementReturned": True}]},
            status_code=200)

        result = data_client.find_framework_suppliers('g-cloud-7')

        assert result == {'supplierFrameworks': [{"agreementReturned": False}, {"agreementReturned": True}]}
        assert rmock.called

    def test_find_framework_suppliers_with_agreement_returned(self, data_client, rmock):
        rmock.get(
            'http://baseurl/frameworks/g-cloud-7/suppliers?agreement_returned=True',
            json={'supplierFrameworks': [{"agreementReturned": False}, {"agreementReturned": True}]},
            status_code=200)

        result = data_client.find_framework_suppliers('g-cloud-7', True)

        assert result == {'supplierFrameworks': [{"agreementReturned": False}, {"agreementReturned": True}]}
        assert rmock.called

    def test_find_framework_suppliers_with_statuses(self, data_client, rmock):
        rmock.get(
            'http://baseurl/frameworks/g-cloud-7/suppliers?status=signed,on-hold',
            json={'supplierFrameworks': [{"agreementReturned": False}, {"agreementReturned": True}]},
            status_code=200)

        result = data_client.find_framework_suppliers('g-cloud-7', statuses='signed,on-hold')

        assert result == {'supplierFrameworks': [{"agreementReturned": False}, {"agreementReturned": True}]}
        assert rmock.called

    def test_put_signed_agreement_on_hold(self, data_client, rmock):
        rmock.post(
            "http://baseurl/agreements/101/on-hold",
            json={'David made me put data in': True},
            status_code=200
        )

        result = data_client.put_signed_agreement_on_hold(101, 'Chris')

        assert result == {'David made me put data in': True}
        assert rmock.call_count == 1
        assert rmock.last_request.json() == {'updated_by': 'Chris'}

    def test_approve_agreement_for_countersignature(self, data_client, rmock):
        rmock.post(
            "http://baseurl/agreements/101/approve",
            json={'David made me put data in': True},
            status_code=200
        )

        result = data_client.approve_agreement_for_countersignature(101, 'chris@example.com', '1234')

        assert result == {'David made me put data in': True}
        assert rmock.call_count == 1
        assert rmock.last_request.json() == {'updated_by': 'chris@example.com', 'agreement': {'userId': '1234'}}

    def test_find_draft_services(self, data_client, rmock):
        rmock.get(
            "http://baseurl/draft-services?supplier_id=2",
            json={"draft-services": "result"},
            status_code=200,
        )

        result = data_client.find_draft_services(
            2, service_id='1234567890123456', framework='g-cloud-6')

        assert result == {"draft-services": "result"}
        assert rmock.called

    def test_get_draft_service(self, data_client, rmock):
        rmock.get(
            "http://baseurl/draft-services/2",
            json={"draft-services": "result"},
            status_code=200,
        )

        result = data_client.get_draft_service(2)

        assert result == {"draft-services": "result"}
        assert rmock.called

    def test_delete_draft_service(self, data_client, rmock):
        rmock.delete(
            "http://baseurl/draft-services/2",
            json={"done": "it"},
            status_code=200,
        )

        result = data_client.delete_draft_service(
            2, 'user'
        )

        assert result == {"done": "it"}
        assert rmock.called
        assert rmock.request_history[0].json() == {
            'updated_by': 'user'
        }

    def test_copy_draft_service_from_existing_service(
            self, data_client, rmock):
        rmock.put(
            "http://baseurl/draft-services/copy-from/2",
            json={"done": "it"},
            status_code=201,
        )

        result = data_client.copy_draft_service_from_existing_service(
            2, 'user'
        )

        assert result == {"done": "it"}
        assert rmock.called
        assert rmock.request_history[0].json() == {
            'updated_by': 'user'
        }

    def test_copy_draft_service(self, data_client, rmock):
        rmock.post(
            "http://baseurl/draft-services/2/copy",
            json={"done": "copy"},
            status_code=201,
        )

        result = data_client.copy_draft_service(2, 'user')

        assert result == {"done": "copy"}
        assert rmock.called
        assert rmock.request_history[0].json() == {
            'updated_by': 'user'
        }

    def test_complete_draft_service(self, data_client, rmock):
        rmock.post(
            "http://baseurl/draft-services/2/complete",
            json={"done": "complete"},
            status_code=201,
        )

        result = data_client.complete_draft_service(2, 'user')

        assert result == {"done": "complete"}
        assert rmock.called
        assert rmock.request_history[0].json() == {
            'updated_by': 'user'
        }

    def test_update_draft_service_status(self, data_client, rmock):
        rmock.post(
            "http://baseurl/draft-services/2/update-status",
            json={"services": {"status": "failed"}},
            status_code=200,
        )

        result = data_client.update_draft_service_status(2, 'failed', 'user')

        assert result == {"services": {"status": "failed"}}
        assert rmock.called
        assert rmock.request_history[0].json() == {
            'updated_by': 'user',
            'services': {'status': 'failed'}
        }

    def test_update_draft_service(self, data_client, rmock):
        rmock.post(
            "http://baseurl/draft-services/2",
            json={"done": "it"},
            status_code=200,
        )

        result = data_client.update_draft_service(
            2, {"field": "value"}, 'user'
        )

        assert result == {"done": "it"}
        assert rmock.called
        assert rmock.request_history[0].json() == {
            'services': {
                "field": "value"
            },
            'updated_by': 'user'
        }

    def test_update_draft_service_with_page_questions(self, data_client, rmock):
        rmock.post(
            "http://baseurl/draft-services/2",
            json={"done": "it"},
            status_code=200,
        )

        result = data_client.update_draft_service(
            2, {"field": "value"}, 'user', ['question1', 'question2']
        )

        assert result == {"done": "it"}
        assert rmock.called
        assert rmock.request_history[0].json() == {
            'services': {
                "field": "value"
            },
            'updated_by': 'user',
            'page_questions': ['question1', 'question2']
        }

    def test_publish_draft_service(self, data_client, rmock):
        rmock.post(
            "http://baseurl/draft-services/2/publish",
            json={"done": "it"},
            status_code=200,
        )

        result = data_client.publish_draft_service(
            2, 'user'
        )

        assert result == {"done": "it"}
        assert rmock.called
        assert rmock.request_history[0].json() == {
            'updated_by': 'user'
        }

    def test_create_new_draft_service(self, data_client, rmock):
        rmock.post(
            "http://baseurl/draft-services",
            json={"done": "it"},
            status_code=201,
        )

        result = data_client.create_new_draft_service(
            'g-cloud-7', 'iaas', 2, {'serviceName': 'name'}, 'user',
        )

        assert result == {"done": "it"}
        assert rmock.called
        assert rmock.request_history[0].json() == {
            'page_questions': [],
            'updated_by': 'user',
            'services': {
                'frameworkSlug': 'g-cloud-7',
                'supplierId': 2,
                'lot': 'iaas',
                'serviceName': 'name',
            }
        }

    def test_find_audit_events(self, data_client, rmock):
        rmock.get(
            "http://baseurl/audit-events",
            json={"audit-event": "result"},
            status_code=200,
        )

        result = data_client.find_audit_events()

        assert result == {"audit-event": "result"}
        assert rmock.called

    def test_find_audit_events_with_audit_type(self, data_client, rmock):
        rmock.get(
            "http://baseurl/audit-events?audit-type=contact_update",
            json={"audit-event": "result"},
            status_code=200,
        )

        result = data_client.find_audit_events(audit_type=AuditTypes.contact_update)

        assert result == {"audit-event": "result"}
        assert rmock.called

    def test_find_audit_events_with_page_and_type(self, data_client, rmock):
        rmock.get(
            "http://baseurl/audit-events?page=123&audit-type=contact_update",
            json={"audit-event": "result"},
            status_code=200,
        )

        result = data_client.find_audit_events(page=123, audit_type=AuditTypes.contact_update)

        assert result == {"audit-event": "result"}
        assert rmock.called

    def test_find_audit_events_with_custom_page_size(self, data_client, rmock):
        rmock.get(
            "http://baseurl/audit-events?per_page=999",
            json={"audit-event": "result"},
            status_code=200)

        result = data_client.find_audit_events(per_page=999)

        assert result == {"audit-event": "result"}
        assert rmock.called

    def test_find_audit_events_with_all_params(self, data_client, rmock):
        rmock.get(
            "http://baseurl/audit-events?page=123&audit-type=contact_update&audit-date=2010-01-01&acknowledged=all&object-type=foo&object-id=123&latest_first=True",  # noqa
            json={"audit-event": "result"},
            status_code=200,
        )

        result = data_client.find_audit_events(
            page=123,
            audit_type=AuditTypes.contact_update,
            acknowledged='all',
            audit_date='2010-01-01',
            object_type='foo',
            object_id=123,
            latest_first=True)

        assert result == {"audit-event": "result"}
        assert rmock.called

    def test_find_audit_events_with_no_none_params(self, data_client, rmock):
        rmock.get(
            "http://baseurl/audit-events?page=123&audit-type=contact_update&acknowledged=all",  # noqa
            json={"audit-event": "result"},
            status_code=200,
        )

        result = data_client.find_audit_events(
            page=123,
            audit_type=AuditTypes.contact_update,
            acknowledged='all',
            audit_date=None)

        assert result == {"audit-event": "result"}
        assert rmock.called

    def test_find_audit_events_with_invalid_audit_type(self, data_client, rmock):
        with pytest.raises(TypeError):
            data_client.find_audit_events(
                page=123,
                audit_type="invalid",
                acknowledged='all',
                audit_date=None)

    def test_acknowledge_audit_event(self, data_client, rmock):
        rmock.post(
            "http://baseurl/audit-events/123/acknowledge",  # noqa
            json={"audit-event": "result"},
            status_code=200,
        )

        result = data_client.acknowledge_audit_event(
            audit_event_id=123,
            user='user')

        assert rmock.called
        assert result == {"audit-event": "result"}
        assert rmock.request_history[0].json() == {
            'updated_by': 'user'
        }

    def test_create_audit_event(self, data_client, rmock):
        rmock.post(
            "http://baseurl/audit-events",
            json={"auditEvents": "result"},
            status_code=201)

        result = data_client.create_audit_event(
            AuditTypes.contact_update, "a user", {"key": "value"}, "suppliers", "123")

        assert rmock.called
        assert result == {'auditEvents': 'result'}
        assert rmock.request_history[0].json() == {
            "auditEvents": {
                "type": "contact_update",
                "user": "a user",
                "data": {"key": "value"},
                "objectType": "suppliers",
                "objectId": "123",
            }
        }

    def test_create_audit_event_with_no_user(self, data_client, rmock):
        rmock.post(
            "http://baseurl/audit-events",
            json={'auditEvents': 'result'},
            status_code=201)

        result = data_client.create_audit_event(
            AuditTypes.contact_update, None, {'key': 'value'}, 'suppliers', '123')

        assert rmock.called
        assert result == {'auditEvents': 'result'}
        assert rmock.request_history[0].json() == {
            "auditEvents": {
                "type": "contact_update",
                "data": {"key": "value"},
                "objectType": "suppliers",
                "objectId": "123",
            }
        }

    def test_create_audit_event_with_no_object(self, data_client, rmock):
        rmock.post(
            "http://baseurl/audit-events",
            json={'auditEvents': 'result'},
            status_code=201)

        result = data_client.create_audit_event(
            AuditTypes.contact_update, 'user', {'key': 'value'})

        assert rmock.called
        assert result == {'auditEvents': 'result'}
        assert rmock.request_history[0].json() == {
            "auditEvents": {
                "type": "contact_update",
                "user": "user",
                "data": {"key": "value"},
            }
        }

    def test_create_audit_with_no_data_defaults_to_empty_object(self, data_client, rmock):
        rmock.post(
            "http://baseurl/audit-events",
            json={'auditEvents': 'result'},
            status_code=201)

        result = data_client.create_audit_event(AuditTypes.contact_update)

        assert rmock.called
        assert result == {'auditEvents': 'result'}
        assert rmock.request_history[0].json() == {
            "auditEvents": {
                "type": "contact_update",
                "data": {},
            }
        }

    def test_create_audit_event_with_invalid_audit_type(self, data_client, rmock):
        rmock.post(
            "http://baseurl/audit-events",
            json={"auditEvents": "result"},
            status_code=200)

        with pytest.raises(TypeError):
            data_client.create_audit_event(
                "thing_happened", "a user", {"key": "value"}, "suppliers", "123")

    def test_get_interested_suppliers(self, data_client, rmock):
        rmock.get(
            'http://baseurl/frameworks/g-cloud-11/interest',
            json={'suppliers': [1, 2]},
            status_code=200)

        result = data_client.get_interested_suppliers('g-cloud-11')

        assert result == {'suppliers': [1, 2]}
        assert rmock.called

    def test_get_framework_stats(self, data_client, rmock):
        rmock.get(
            'http://baseurl/frameworks/g-cloud-11/stats',
            json={'drafts': 1},
            status_code=200)

        result = data_client.get_framework_stats('g-cloud-11')

        assert result == {'drafts': 1}
        assert rmock.called

    def test_get_framework_stats_raises_on_error(self, data_client, rmock):
        with pytest.raises(APIError):
            rmock.get(
                'http://baseurl/frameworks/g-cloud-11/stats',
                json={'drafts': 1},
                status_code=400)

            data_client.get_framework_stats('g-cloud-11')

    def test_find_frameworks(self, data_client, rmock):
        rmock.get(
            'http://baseurl/frameworks',
            json={'frameworks': ['g6', 'g7']},
            status_code=200)

        result = data_client.find_frameworks()

        assert result == {'frameworks': ['g6', 'g7']}
        assert rmock.called

    def test_get_framework(self, data_client, rmock):
        rmock.get(
            'http://baseurl/frameworks/g-cloud-11',
            json={'frameworks': {'g-cloud-11': 'yes'}},
            status_code=200)

        result = data_client.get_framework('g-cloud-11')

        assert result == {'frameworks': {'g-cloud-11': 'yes'}}
        assert rmock.called

    def test_create_brief(self, data_client, rmock):
        rmock.post(
            "http://baseurl/briefs",
            json={"briefs": "result"},
            status_code=201,
        )

        result = data_client.create_brief(
            "digital-things", "digital-watches", 123,
            {"title": "Timex"},
            "user@email.com",
            page_questions=["title"])

        assert result == {"briefs": "result"}
        assert rmock.last_request.json() == {
            "briefs": {
                "frameworkSlug": "digital-things",
                "lot": "digital-watches",
                "userId": 123,
                "title": "Timex"
            },
            "page_questions": ["title"],
            "updated_by": "user@email.com"
        }

    def test_update_brief(self, data_client, rmock):
        rmock.post(
            "http://baseurl/briefs/123",
            json={"briefs": "result"},
            status_code=200,
        )

        result = data_client.update_brief(123, {"foo": "bar"}, "user@email.com")

        assert result == {"briefs": "result"}
        assert rmock.last_request.json() == {
            "briefs": {"foo": "bar"},
            "page_questions": [],
            "updated_by": "user@email.com"
        }

    def test_publish_brief(self, data_client, rmock):
        rmock.post(
            "http://baseurl/briefs/123/publish",
            json={"briefs": "result"},
            status_code=200,
        )

        result = data_client.publish_brief(123, "user@email.com")

        assert result == {"briefs": "result"}
        assert rmock.last_request.json() == {
            "updated_by": "user@email.com"
        }

    def test_get_brief(self, data_client, rmock):
        rmock.get(
            "http://baseurl/briefs/123",
            json={"briefs": "result"},
            status_code=200)

        result = data_client.get_brief(123)

        assert result == {"briefs": "result"}

    def test_find_briefs(self, data_client, rmock):
        rmock.get(
            "http://baseurl/briefs",
            json={"briefs": []},
            status_code=200)

        result = data_client.find_briefs(user_id=123)

        assert rmock.called
        assert result == {"briefs": []}

    def test_find_briefs_for_user(self, data_client, rmock):
        rmock.get(
            "http://baseurl/briefs?user_id=123",
            json={"briefs": []},
            status_code=200)

        result = data_client.find_briefs(user_id=123)

        assert rmock.called
        assert result == {"briefs": []}

    def test_find_briefs_by_lot_status_framework_and_human_readable(self, data_client, rmock):
        rmock.get(
            "http://baseurl/briefs?status=live,closed&framework=digital-biscuits&lot=custard-creams&human=true",
            json={"briefs": [{"biscuit": "tasty"}]},
            status_code=200)

        result = data_client.find_briefs(status="live,closed", framework="digital-biscuits", lot="custard-creams",
                                         human=True)

        assert rmock.called
        assert result == {"briefs": [{"biscuit": "tasty"}]}

    def test_find_briefs_with_users(self, data_client, rmock):
        rmock.get(
            "http://baseurl/briefs?with_users=True",
            json={"briefs": [{"biscuit": "tasty"}]},
            status_code=200)

        result = data_client.find_briefs(with_users=True)

        assert rmock.called
        assert result == {"briefs": [{"biscuit": "tasty"}]}

    def test_delete_brief(self, data_client, rmock):
        rmock.delete(
            "http://baseurl/briefs/2",
            json={"done": "it"},
            status_code=200,
        )

        result = data_client.delete_brief(
            2, 'user'
        )

        assert result == {"done": "it"}
        assert rmock.called
        assert rmock.request_history[0].json() == {
            'updated_by': 'user'
        }

    def test_is_supplier_eligible_for_brief(self, data_client, rmock):
        rmock.get(
            "http://baseurl/briefs/456/services?supplier_id=123",
            json={"services": ["one"]},
            status_code=200)

        result = data_client.is_supplier_eligible_for_brief(123, 456)

        assert result is True

    def test_supplier_ineligible_for_brief(self, data_client, rmock):
        rmock.get(
            "http://baseurl/briefs/456/services?supplier_id=123",
            json={"services": []},
            status_code=200)

        result = data_client.is_supplier_eligible_for_brief(123, 456)

        assert result is False

    def test_create_brief_response_with_page_questions(self, data_client, rmock):
        rmock.post(
            "http://baseurl/brief-responses",
            json={"briefs": "result"},
            status_code=201,
        )

        result = data_client.create_brief_response(
            1, 2, {"essentialRequirements": [True, None, False]}, "user@email.com", page_questions=['question']
        )

        assert result == {"briefs": "result"}
        assert rmock.last_request.json() == {
            "briefResponses": {
                "briefId": 1,
                "supplierId": 2,
                "essentialRequirements": [True, None, False],
            },
            "page_questions": ['question'],
            "updated_by": "user@email.com"
        }

    def test_create_brief_response_without_page_questions(self, data_client, rmock):
        rmock.post(
            "http://baseurl/brief-responses",
            json={"briefs": "result"},
            status_code=201,
        )

        result = data_client.create_brief_response(
            1, 2, {"essentialRequirements": [True, None, False]}, "user@email.com"
        )

        assert result == {"briefs": "result"}
        assert rmock.last_request.json() == {
            "briefResponses": {
                "briefId": 1,
                "supplierId": 2,
                "essentialRequirements": [True, None, False],
            },
            "page_questions": [],
            "updated_by": "user@email.com"
        }

    def test_update_brief_response(self, data_client, rmock):
        rmock.post(
            "http://baseurl/brief-responses/1234",
            json={"briefs": "result"},
            status_code=200,
        )

        result = data_client.update_brief_response(
            1234,
            {'email_address': 'test@example.com'},
            'user@example.com',
            ['email_address']
        )

        assert result == {"briefs": "result"}
        assert rmock.last_request.json() == {
            "briefResponses": {
                'email_address': 'test@example.com'
            },
            "page_questions": ['email_address'],
            "updated_by": "user@example.com"
        }

    def test_submit_brief_response(self, data_client, rmock):
        rmock.post(
            "http://baseurl/brief-responses/123/submit",
            json={"briefResponses": "result"},
            status_code=200,
        )

        result = data_client.submit_brief_response(123, "user@email.com")

        assert result == {"briefResponses": "result"}

        assert rmock.last_request.json() == {
            "updated_by": "user@email.com"
        }

    def test_get_brief_response(self, data_client, rmock):
        rmock.get(
            "http://baseurl/brief-responses/123",
            json={"briefResponses": "result"},
            status_code=200)

        result = data_client.get_brief_response(123)

        assert result == {"briefResponses": "result"}

    def test_find_brief_responses(self, data_client, rmock):
        rmock.get(
            "http://baseurl/brief-responses?brief_id=1&supplier_id=2&status=draft",
            json={"briefResponses": []},
            status_code=200)

        result = data_client.find_brief_responses(brief_id=1, supplier_id=2, status='draft')

        assert result == {"briefResponses": []}

    def test_add_brief_clarification_question(self, data_client, rmock):
        rmock.post(
            "http://baseurl/briefs/1/clarification-questions",
            json={"briefs": "result"},
            status_code=200)

        result = data_client.add_brief_clarification_question(1, "Why?", "Because", "user@example.com")

        assert result == {"briefs": "result"}
        assert rmock.last_request.json() == {
            "clarificationQuestion": {"question": "Why?", "answer": "Because"},
            "updated_by": "user@example.com",
        }

    def test_get_framework_agreement(self, data_client, rmock):
        rmock.get(
            "http://baseurl/agreements/12345",
            json={"agreement": {'details': 'here'}},
            status_code=200)

        result = data_client.get_framework_agreement(12345)

        assert result == {"agreement": {'details': 'here'}}

    def test_create_framework_agreement(self, data_client, rmock):
        rmock.post(
            "http://baseurl/agreements",
            json={"agreement": {'details': 'here'}},
            status_code=201)

        result = data_client.create_framework_agreement(10, 'g-cloud-8', "user@example.com")

        assert result == {"agreement": {'details': 'here'}}
        assert rmock.last_request.json() == {
            "agreement": {"supplierId": 10, "frameworkSlug": "g-cloud-8"},
            "updated_by": "user@example.com",
        }

    def test_update_framework_agreement(self, data_client, rmock):
        rmock.post(
            "http://baseurl/agreements/12345",
            json={"agreement": {'details': 'here'}},
            status_code=200)

        result = data_client.update_framework_agreement(12345, {"new": "details"}, "user@example.com")

        assert result == {"agreement": {'details': 'here'}}
        assert rmock.last_request.json() == {
            "agreement": {"new": "details"},
            "updated_by": "user@example.com",
        }

    def test_sign_framework_agreement_with_no_signed_agreement_details(self, data_client, rmock):
        rmock.post(
            "http://baseurl/agreements/12345/sign",
            json={"agreement": {'response': 'here'}},
            status_code=200)

        result = data_client.sign_framework_agreement(12345, "user@example.com")

        assert result == {"agreement": {'response': 'here'}}
        assert rmock.last_request.json() == {
            "updated_by": "user@example.com",
        }

    def test_sign_framework_agreement_with_signed_agreement_details(self, data_client, rmock):
        rmock.post(
            "http://baseurl/agreements/12345/sign",
            json={"agreement": {'response': 'here'}},
            status_code=200)

        result = data_client.sign_framework_agreement(12345, "user@example.com", {"uploaderUserId": 20})

        assert result == {"agreement": {'response': 'here'}}
        assert rmock.last_request.json() == {
            "agreement": {"signedAgreementDetails": {"uploaderUserId": 20}},
            "updated_by": "user@example.com",
        }


class TestDataAPIClientIterMethods(object):
    def _test_find_iter(self, data_client, rmock, method_name, model_name, url_path):
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

        result = getattr(data_client, method_name)()
        results = list(result)

        assert len(results) == 3
        assert results[0]['id'] == 1
        assert results[1]['id'] == 2
        assert results[2]['id'] == 3

    def test_find_users_iter(self, data_client, rmock):
        self._test_find_iter(
            data_client, rmock,
            method_name='find_users_iter',
            model_name='users',
            url_path='users')

    def test_find_briefs_iter(self, data_client, rmock):
        self._test_find_iter(
            data_client, rmock,
            method_name='find_briefs_iter',
            model_name='briefs',
            url_path='briefs')

    def test_find_brief_responses_iter(self, data_client, rmock):
        self._test_find_iter(
            data_client, rmock,
            method_name='find_brief_responses_iter',
            model_name='briefResponses',
            url_path='brief-responses')

    def test_find_audit_events_iter(self, data_client, rmock):
        self._test_find_iter(
            data_client, rmock,
            method_name='find_audit_events_iter',
            model_name='auditEvents',
            url_path='audit-events')

    def test_find_suppliers_iter(self, data_client, rmock):
        self._test_find_iter(
            data_client, rmock,
            method_name='find_suppliers_iter',
            model_name='suppliers',
            url_path='suppliers')

    def test_find_draft_services_iter(self, data_client, rmock):
        rmock.get(
            'http://baseurl/draft-services?supplier_id=123',
            json={
                'links': {'next': 'http://baseurl/draft-services?supplier_id=123&page=2'},
                'services': [{'id': 1}, {'id': 2}]
            },
            status_code=200)
        rmock.get(
            'http://baseurl/draft-services?supplier_id=123&page=2',
            json={
                'links': {'prev': 'http://baseurl/draft-services?supplier_id=123'},
                'services': [{'id': 3}]
            },
            status_code=200)

        result = data_client.find_draft_services_iter(123)
        results = list(result)

        assert len(results) == 3
        assert results[0]['id'] == 1
        assert results[1]['id'] == 2
        assert results[2]['id'] == 3

    def test_find_services_iter(self, data_client, rmock):
        self._test_find_iter(
            data_client, rmock,
            method_name='find_services_iter',
            model_name='services',
            url_path='services')

    def test_find_services_iter_additional_arguments(self, data_client, rmock):
        rmock.get(
            'http://baseurl/services?supplier_id=123',
            json={
                'links': {},
                'services': [{'id': 1}, {'id': 2}]
            },
            status_code=200)

        result = data_client.find_services_iter(123)
        results = list(result)

        assert len(results) == 2

    @mock.patch('time.sleep')
    def test_find_services_backoff_on_503(self, sleep, data_client, rmock):
        rmock.get(
            'http://baseurl/services',
            [{'json': {}, 'status_code': 503},
             {'json': {'links': {}, 'services': [{'id': 1}]}, 'status_code': 200}])

        result = data_client.find_services_iter()
        results = list(result)

        assert sleep.called
        assert len(results) == 1
