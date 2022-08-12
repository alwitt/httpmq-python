"""Wrapper object for operating the httpmq management API"""

from typing import Dict, Tuple

from httpmq.common import RequestContext


class MgmtAPIWrapper:
    """Client wrapper object for operating the httpmq management API"""

    def __init__(self, api_client):
        """Constructor

        :param api_client: base client object for interacting with httpmq
        """

    def ready(self, ctxt: RequestContext):
        """Check whether the httpmq management API is ready. Raise exception if not.

        :param ctxt: the caller context
        """

    #####################################################################################
    # Stream related API functions

    def create_stream(self, params, ctxt: RequestContext) -> str:
        """Define a new stream

        :param params: the new stream parameters
        :param ctxt: the caller context
        :return: request ID in the response
        """

    def list_all_streams(self, ctxt: RequestContext) -> Tuple[Dict[str, object], str]:
        """Query for list of all known streams

        :param ctxt: the caller context
        :return: list of known streams, and request ID in the response
        """

    def get_stream(self, stream: str, ctxt: RequestContext) -> Tuple[object, str]:
        """Query for a particular stream

        :param stream: the stream to query for
        :param ctxt: the caller context
        :return: information on the stream, and request ID in the response
        """

    def change_stream_subjects(
        self, stream: str, new_subjects: list, ctxt: RequestContext
    ) -> str:
        """Change the target subjects of a stream

        :param stream: name of the stream
        :param ctxt: the caller context
        :return: request ID in the response
        """

    def update_stream_limits(self, stream: str, limits, ctxt: RequestContext) -> str:
        """Update the data retention limits of a stream

        :param stream: name of the stream
        :param limits: new data retention limits
        :param ctxt: the caller context
        :return: request ID in the response
        """

    def delete_stream(self, stream: str, ctxt: RequestContext) -> str:
        """Delete a stream

        :param stream: name of the stream
        :param ctxt: the caller context
        :return: request ID in the response
        """

    #####################################################################################
    # Consumer related API functions

    def create_consumer_for_stream(
        self,
        stream: str,
        params,
        ctxt: RequestContext,
    ) -> str:
        """Define a new customer on a stream

        :param stream: the stream to create the consumer on
        :param params: the consumer parameters
        :param ctxt: the caller context
        :return: request ID in the response
        """

    def list_all_consumer_of_stream(
        self,
        stream: str,
        ctxt: RequestContext,
    ) -> Tuple[Dict[str, object], str]:
        """List of all known consumers on a stream

        :param stream: the stream to query for
        :param ctxt: the caller context
        :return: list of known consumers of a stream, and request ID in the response
        """

    def get_consumer_of_stream(
        self, stream: str, consumer: str, ctxt: RequestContext
    ) -> Tuple[object, str]:
        """Query for a particular consumer on a stream

        :param stream: name of the stream
        :param consumer: name of the consumer
        :param ctxt: the caller context
        :return: information on a consumer, and request ID in the response
        """

    def delete_consumer_on_stream(
        self, stream: str, consumer: str, ctxt: RequestContext
    ):
        """Delete a consumer on a stream

        :param stream: name of the stream
        :param consumer: name of the consumer
        :param ctxt: the caller context
        :return: request ID in the response
        """
