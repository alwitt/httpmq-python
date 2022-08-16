"""Wrapper object for operating the httpmq dataplane API"""

# pylint: disable=too-many-arguments
# pylint: disable=too-few-public-methods
# pylint: disable=too-many-locals

import asyncio
from http import HTTPStatus
import json
from httpmq import client
from httpmq.common import HttpmqAPIError, RequestContext
from httpmq.models import (
    GoutilsRestAPIBaseResponse,
)


class ReceivedMessage:
    """Container for a received message"""

    def __init__(
        self,
        stream: str,
        stream_seq: int,
        consumer: str,
        consumer_seq: int,
        subject: str,
        message: bytes,
        request_id: str,
    ):
        """Constructor

        :param stream: name of the stream this message is from
        :param stream_seq: the message sequence number within this stream
        :param consumer: name of the consumer that received the message
        :param consumer_seq: the message sequence number for that consumer on this stream
        :param subject: the message subject
        :param request_id: request ID
        """
        self.stream = stream
        self.stream_seq = stream_seq
        self.consumer = consumer
        self.consumer_seq = consumer_seq
        self.subject = subject
        self.message = message
        self.request_id = request_id


class DataAPIWrapper:
    """Client wrapper object for operating the httpmq dataplane API"""

    # Endpoints of the management API
    PATH_READY = "/v1/data/ready"

    def __init__(self, api_client: client.APIClient):
        """Constructor

        :param api_client: base client object for interacting with httpmq
        """
        self.client = api_client

    async def ready(self, context: RequestContext):
        """Check whether the httpmq dataplane API is ready. Raise exception if not.

        :param context: the caller context
        """
        resp = await self.client.get(path=DataAPIWrapper.PATH_READY, context=context)
        if resp.status != HTTPStatus.OK:
            raise HttpmqAPIError(
                request_id=context.request_id,
                status_code=resp.status,
                message="management API is not ready",
            )
        # Process the response body
        parsed = GoutilsRestAPIBaseResponse.from_dict(json.loads(resp.content))
        if not parsed.success:
            raise HttpmqAPIError.from_rest_base_api_response(parsed)

    async def publish(
        self, subject: str, message: bytes, context: RequestContext
    ) -> str:
        """Publishes a message under a subject

        :param subject: the subject to publish under
        :param message: the message to publish
        :param context: the caller context
        :return: request ID in the response
        """

    async def send_ack(
        self,
        stream: str,
        stream_seq: int,
        consumer: str,
        consumer_seq: int,
        context: RequestContext,
    ) -> str:
        """Send a message ACK for an associated JetStream message

        Each message is marked by two sequence numbers.
          * the stream sequence number
          * the consumer sequence number

        The stream sequence number is the global ID of a message within the stream. Each
        message receives a unique monotonically increasing stream sequence number.

        The consumer sequence number tracks the messages sent to a consumer from a stream;
        the consumer has per-stream sequence number tracking for each stream the consumer
        listens to.

        Each time a consumer receives a message from the stream (a new message, or a retransmit
        of a previous message), that consumer's sequence number on that stream is increased.

        :param stream: name of the stream this message is from
        :param stream_seq: the message sequence number within this stream
        :param consumer: name of the consumer that received the message
        :param consumer_seq: the message sequence number for that consumer on this stream
        :param context: the caller context
        :return: request ID in the response
        """

    async def push_subscribe(
        self,
        stream: str,
        consumer: str,
        subject_filter: str,
        forward_data_cb,
        context: RequestContext,
        stop_loop: asyncio.Event,
        max_msg_inflight: int = None,
        delivery_group: str = None,
        loop_interval_sec: float = 0.25,
    ) -> str:
        """Start a push subscription for a consumer on a stream

        This is a blocking function which only exits when either
          * The caller request the loop to stop
          * Some error occurs
          * The server closes the connection

        The receives messages are passed back via a call-back function.

        The loop uses non-blocking read function, so it sleeps between reads.

        :param stream: target stream
        :param consumer: consumer name
        :param subject_filter: subscribe for message which subject matches the filter
        :param forward_data_cb: callback function used to forward data back to the caller
        :param context: the caller context
        :param stop_loop: signal to indicate the loop should stop
        :param max_msg_inflight: the max number of inflight messages if provided
        :param delivery_group: the delivery group the consumer belongs to if the consumer uses one
        :param loop_interval_sec: the sleep interval between non-blocking reads
        :return: request ID in the response
        """
