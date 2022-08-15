"""Wrapper object for operating the httpmq management API"""

from http import HTTPStatus
import json
from typing import Dict, Tuple

from httpmq import client
from httpmq.common import HttpmqAPIError, RequestContext
from httpmq.models import GoutilsRestAPIBaseResponse


class MgmtAPIWrapper:
    """Client wrapper object for operating the httpmq management API"""

    # Endpoints of the management API
    PATH_READY = "/v1/admin/ready"

    def __init__(self, api_client: client.APIClient):
        """Constructor

        :param api_client: base client object for interacting with httpmq
        """
        self.client = api_client

    async def ready(self, context: RequestContext):
        """Check whether the httpmq management API is ready. Raise exception if not.

        :param context: the caller context
        """
        resp = await self.client.get(path=MgmtAPIWrapper.PATH_READY, context=context)
        if resp.status != HTTPStatus.OK:
            raise HttpmqAPIError(
                request_id=context.request_id,
                status_code=resp.status,
                message="management API is not ready",
            )
        # Process the message body
        parsed = GoutilsRestAPIBaseResponse.from_dict(json.loads(resp.content))
        if not parsed.success:
            raise HttpmqAPIError.from_rest_base_api_response(parsed)

    #####################################################################################
    # Stream related API functions

    async def create_stream(self, params, context: RequestContext) -> str:
        """Define a new stream

        :param params: the new stream parameters
        :param context: the caller context
        :return: request ID in the response
        """

    async def list_all_streams(
        self, context: RequestContext
    ) -> Tuple[Dict[str, object], str]:
        """Query for list of all known streams

        :param context: the caller context
        :return: list of known streams, and request ID in the response
        """

    async def get_stream(
        self, stream: str, context: RequestContext
    ) -> Tuple[object, str]:
        """Query for a particular stream

        :param stream: the stream to query for
        :param context: the caller context
        :return: information on the stream, and request ID in the response
        """

    async def change_stream_subjects(
        self, stream: str, new_subjects: list, context: RequestContext
    ) -> str:
        """Change the target subjects of a stream

        :param stream: name of the stream
        :param context: the caller context
        :return: request ID in the response
        """

    async def update_stream_limits(
        self, stream: str, limits, context: RequestContext
    ) -> str:
        """Update the data retention limits of a stream

        :param stream: name of the stream
        :param limits: new data retention limits
        :param context: the caller context
        :return: request ID in the response
        """

    async def delete_stream(self, stream: str, context: RequestContext) -> str:
        """Delete a stream

        :param stream: name of the stream
        :param context: the caller context
        :return: request ID in the response
        """

    #####################################################################################
    # Consumer related API functions

    async def create_consumer_for_stream(
        self,
        stream: str,
        params,
        context: RequestContext,
    ) -> str:
        """Define a new customer on a stream

        :param stream: the stream to create the consumer on
        :param params: the consumer parameters
        :param context: the caller context
        :return: request ID in the response
        """

    async def list_all_consumer_of_stream(
        self,
        stream: str,
        context: RequestContext,
    ) -> Tuple[Dict[str, object], str]:
        """List of all known consumers on a stream

        :param stream: the stream to query for
        :param context: the caller context
        :return: list of known consumers of a stream, and request ID in the response
        """

    async def get_consumer_of_stream(
        self, stream: str, consumer: str, context: RequestContext
    ) -> Tuple[object, str]:
        """Query for a particular consumer on a stream

        :param stream: name of the stream
        :param consumer: name of the consumer
        :param context: the caller context
        :return: information on a consumer, and request ID in the response
        """

    async def delete_consumer_on_stream(
        self, stream: str, consumer: str, context: RequestContext
    ):
        """Delete a consumer on a stream

        :param stream: name of the stream
        :param consumer: name of the consumer
        :param context: the caller context
        :return: request ID in the response
        """
