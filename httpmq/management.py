"""Wrapper object for operating the httpmq management API"""

from httpmq.core import ApiClient
from httpmq.core.api.management_api import ManagementApi
from httpmq.core.models import (
    ManagementJSStreamParam,
    ManagementJSStreamLimits,
    GoutilsRestAPIBaseResponse,
)
from .common import APICallContext, HttpmqAPIError


class MgmtAPIWrapper:
    """Client wrapper object for operating the httpmq management API"""

    def __init__(self, api_client: ApiClient):
        """Constructor

        :param api_client: base client object for interacting with httpmq
        """
        self.client = ManagementApi(api_client=api_client)

    def ready(self, ctxt: APICallContext):
        """Check whether the httpmq management API is ready. Raise exception if not.

        :param ctxt: the caller context
        """
        response: GoutilsRestAPIBaseResponse = self.client.v1_admin_ready_get(
            async_req=False,
            _request_timeout=ctxt.request_timeout_sec,
            _request_auths=ctxt.auth_param,
        )
        # Not ready
        if not response.success:
            raise HttpmqAPIError(
                request_id=response.request_id,
                status_code=response.error.code,
                message=(
                    response.error.message
                    if hasattr(response.error, "message")
                    else None
                ),
                detail=(
                    response.error.detail if hasattr(response.error, "detail") else None
                ),
            )

    #####################################################################################
    # Stream related API functions

    def create_stream(self, params: ManagementJSStreamParam, ctxt: APICallContext):
        """Define a new stream

        :param params: the new stream parameters
        :param ctxt: the caller context
        :return: request ID (to reference logs)
        """

    def list_all_streams(self, ctxt: APICallContext):
        """Query for list of all known streams

        :param ctxt: the caller context
        :return: request ID (to reference logs), list of known streams
        """

    def get_stream(self, stream: str, ctxt: APICallContext):
        """Query for a particular stream

        :param stream: the stream to query for
        :param ctxt: the caller context
        :return: request ID (to reference logs), information on the stream
        """

    def change_stream_subjects(
        self, stream: str, new_subjects: list, ctxt: APICallContext
    ):
        """Change the target subjects of a stream

        :param stream: name of the stream
        :param ctxt: the caller context
        :return: request ID (to reference logs)
        """

    def update_stream_limits(
        self, stream: str, limits: ManagementJSStreamLimits, ctxt: APICallContext
    ):
        """Update the data retention limits of a stream

        :param stream: name of the stream
        :param limits: new data retention limits
        :param ctxt: the caller context
        :return: request ID (to reference logs)
        """

    def delete_stream(self, stream: str, ctxt: APICallContext):
        """Delete a stream

        :param stream: name of the stream
        :param ctxt: the caller context
        :return: request ID (to reference logs)
        """
