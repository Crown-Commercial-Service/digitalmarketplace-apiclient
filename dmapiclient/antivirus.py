from .base import BaseAPIClient


class AntivirusAPIClient(BaseAPIClient):
    def init_app(self, app):
        self._base_url = app.config['DM_ANTIVIRUS_API_URL']
        self._auth_token = app.config['DM_ANTIVIRUS_API_AUTH_TOKEN']

    def scan_and_tag_s3_object(self, bucket_name, object_key, object_version_id):
        return self._put(
            "/scan/s3-object",
            data={
                "bucketName": bucket_name,
                "objectKey": object_key,
                "objectVersionId": object_version_id,
            },
        )
