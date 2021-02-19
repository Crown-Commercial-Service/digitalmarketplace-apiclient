from typing import Union

REQUEST_ERROR_STATUS_CODE = 503
REQUEST_ERROR_MESSAGE = "Unknown request failure in dmapiclient"


class APIError(Exception):
    def __init__(self, response=None, message=None):
        self.response = response
        self._message = message

    @property
    def message(self) -> Union[str, dict]:
        try:
            return self.response.json()['error']
        except (TypeError, ValueError, AttributeError, KeyError):
            return self._message or REQUEST_ERROR_MESSAGE

    @property
    def status_code(self) -> int:
        try:
            return self.response.status_code
        except AttributeError:
            return REQUEST_ERROR_STATUS_CODE

    def __str__(self):
        return "{} (status: {})".format(self.message, self.status_code)


class HTTPError(APIError):
    @staticmethod
    def create(e):
        fallback_message = '{}\n{}'.format(str(e), repr(e))

        return HTTPError(e.response, fallback_message)


class InvalidResponse(APIError):
    pass
