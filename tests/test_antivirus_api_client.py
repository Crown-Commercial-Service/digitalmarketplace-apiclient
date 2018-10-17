import pytest
import mock

from dmapiclient import AntivirusAPIClient


@pytest.fixture
def antivirus_client():
    return AntivirusAPIClient('http://baseurl', 'auth-token', True)


class TestAntivirusApiClient(object):
    def test_init_app_sets_attributes(self, antivirus_client):
        app = mock.Mock()
        app.config = {
            "DM_ANTIVIRUS_API_URL": "http://example",
            "DM_ANTIVIRUS_API_AUTH_TOKEN": "example-token",
        }
        antivirus_client.init_app(app)

        assert antivirus_client.base_url == "http://example"
        assert antivirus_client.auth_token == "example-token"

    def test_get_status(self, antivirus_client, rmock):
        rmock.get(
            "http://baseurl/_status",
            json={"status": "ok"},
            status_code=200,
        )

        result = antivirus_client.get_status()

        assert result['status'] == "ok"
        assert rmock.called


class TestServiceMethods(object):
    def test_scan_and_tag_s3_object(self, antivirus_client, rmock):
        rmock.put(
            "http://baseurl/scan/s3-object",
            json={"Clappy": "clapclap"},
            status_code=200,
        )

        result = antivirus_client.scan_and_tag_s3_object(
            bucket_name="Clapclipclap",
            object_key="Clapclopclap",
            object_version_id="enclap",
        )

        assert result == {"Clappy": "clapclap"}
        assert rmock.last_request.json() == {
            "bucketName": "Clapclipclap",
            "objectKey": "Clapclopclap",
            "objectVersionId": "enclap",
        }
