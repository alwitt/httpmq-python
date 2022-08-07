"""Wrapper object for operating the httpmq dataplane API"""

from httpmq.core import ApiClient
from httpmq.core.api.dataplane_api import DataplaneApi
from httpmq.core.models import (
    GoutilsRestAPIBaseResponse,
)
from .common import APICallContext, HttpmqAPIError


class DataAPIWrapper:
    """Client wrapper object for operating the httpmq dataplane API"""

    def __init__(self, api_client: ApiClient):
        """Constructor

        :param api_client: base client object for interacting with httpmq
        """
        self.client = DataplaneApi(api_client=api_client)

    def ready(self, ctxt: APICallContext):
        """Check whether the httpmq dataplane API is ready. Raise exception if not.

        :param ctxt: the caller context
        """
        response: GoutilsRestAPIBaseResponse = self.client.v1_data_ready_get(
            async_req=False,
            _request_timeout=ctxt.request_timeout_sec,
            _request_auths=ctxt.auth_param,
        )
        # Not ready
        if not response.success:
            raise HttpmqAPIError.new_error(response)
