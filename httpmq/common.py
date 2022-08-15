"""Support classes and functions"""


import uuid
import aiohttp
from multidict import CIMultiDict, CIMultiDictProxy

from httpmq import DEFAULT_REQUEST_ID_FIELD


class RequestContext:
    """
    API request context provides
      * Call authorization header param
      * Additional HTTP headers
      * Metadata associated with a call

    :param auth_param: authentication parameters for use with the call
    :param request_timeout_sec: If set, the number of seconds (as float) before timeout
    """

    def __init__(self, request_id_field: str = DEFAULT_REQUEST_ID_FIELD):
        """Constructor

        :param request_id_field: the HTTP field to send a request as
        """
        self.auth_param = {"header": [], "param": []}
        self.additional_headers = CIMultiDict()
        self.additional_params = {}
        self.request_timeout = None
        self.request_id_field = request_id_field
        self.request_id = str(uuid.uuid4())

    def get_headers(self) -> CIMultiDictProxy:
        """Fetch the headers unique to this request

        :return: the additional headers
        """
        all_headers = CIMultiDict()
        # Add the additional headers
        all_headers.extend(CIMultiDictProxy(self.additional_headers))
        # Add the request ID
        all_headers.add(self.request_id_field, self.request_id)
        # Add the authorization header
        for one_auth_entry in self.auth_param["header"]:
            all_headers.add("Authorization", one_auth_entry)
        return all_headers

    def add_header_auth_token(self, token_with_type: str):
        """Record a header auth token for use in a request

        :param token_with_type: the authentication token with type (i.e. Bearer ########)
        """
        self.auth_param["header"].append(token_with_type)
        return self

    def add_header(self, header_name: str, header_value: str):
        """Add header to request

        :param header_name: HTTP header name
        :param header_value: HTTP header value
        """
        self.additional_headers.add(header_name, header_value)
        return self

    def add_param(self, param_name: str, param_value: str):
        """Add URL parameter to request

        :param param_name: URL parameter name
        :param param_value: parameter value
        """
        self.additional_params[param_name] = param_value
        return self

    def set_request_timeout(self, timeout: aiohttp.ClientTimeout):
        """Set the request timeout

        :param timeout: request timeout
        """
        self.request_timeout = timeout
        return self

    def set_request_id(self, request_id: str):
        """Set the request ID

        :param id: the request ID to use for the request
        """
        self.request_id = request_id
        return self


class HttpmqException(Exception):
    """Base exception class for HTTP MQ client operations"""


class HttpmqAPIError(HttpmqException):
    """Custom error returned by httpmq"""

    def __init__(
        self, request_id: str, status_code: int, message: str = None, detail: str = None
    ):
        """Constructor

        :param request_id: the request ID to match against logs
        :param status_code: response code returned by httpmq
        :param message: optional descriptive message
        :param detail: optional descriptive message providing additional details
        """
        self.request_id = request_id
        self.status_code = status_code
        self.message = message
        self.detail = detail
        full_msg = f"Request '{request_id}' failed with ({status_code})"
        if message is not None:
            full_msg += f" because of [{message}]"
        if detail is not None:
            full_msg += f": {detail}"
        super().__init__(full_msg)

    @staticmethod
    def from_rest_base_api_response(resp):
        """Define HttpmqAPIError from a models/{{ object }} which contain components of
        GoutilsRestAPIBaseResponse.

        :param resp: the response structure
        """
        return HttpmqAPIError(
            request_id=resp.request_id,
            status_code=resp.error.code,
            message=resp.error.message,
            detail=resp.error.detail,
        )
