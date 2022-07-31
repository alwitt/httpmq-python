"""Support classes and functions"""


import uuid


class APICallContext:
    """
    API call context provides
      * Call authorization header param
      * Additional HTTP headers
      * Metadata associated with a call

    :param auth_param: authentication parameters for use with the call
    :param request_timeout_sec: If set, the number of seconds (as float) before timeout
    """

    def __init__(self):
        """Constructor"""
        self.auth_param = []
        self.request_timeout_sec = None
        self.request_id = str(uuid.uuid4())

    def add_bearer_auth_token(self, token: str):
        """Record a bearer auth token for use in a request

        :param token: the bearer authentication token
        """
        self.auth_param.append(
            {
                "in": "header",
                "type": "bearer",
                "key": "Authorization",
                "value": f"Bearer {token}",
            }
        )

    def set_request_timeout(self, timeout_sec: float):
        """Set the request timeout

        :param timeout_sec: the number of seconds before request timeout
        """
        self.request_timeout_sec = timeout_sec

    def set_request_id(self, request_id: str):
        """Set the request ID

        :param id: the request ID to use for the request
        """
        self.request_id = request_id


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
    def new_error(call_response):
        """Generate a new error

        :param call_response: the request response
        :return: a new error object
        """
        return HttpmqAPIError(
            request_id=call_response.request_id,
            status_code=call_response.error.code,
            message=(
                call_response.error.message
                if hasattr(call_response.error, "message")
                else None
            ),
            detail=(
                call_response.error.detail
                if hasattr(call_response.error, "detail")
                else None
            ),
        )
