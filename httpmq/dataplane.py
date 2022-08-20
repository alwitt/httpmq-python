"""Wrapper object for operating the httpmq dataplane API"""

# pylint: disable=too-many-arguments
# pylint: disable=too-few-public-methods
# pylint: disable=too-many-locals

import asyncio
import base64
from http import HTTPStatus
import json
import logging
from typing import Dict, List, Union
from httpmq import client
from httpmq.common import HttpmqInternalError, HttpmqAPIError, RequestContext
from httpmq.models import (
    ApisAPIRestRespDataMessage,
    DataplaneAckSeqNum,
    GoutilsRestAPIBaseResponse,
)

LOG = logging.getLogger("httpmq-sdk.dataplane")


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


class DataClient:
    """Client wrapper object for operating the httpmq dataplane API"""

    # Endpoints of the management API
    PATH_READY = "/v1/data/ready"
    PATH_PUBLISH_BASE = "/v1/data/subject"
    PATH_SUBSCRIBE_BASE = "/v1/data/stream"

    @staticmethod
    def __publish_path(subject: str) -> str:
        """Helper function to compute the endpoint path for message publish"""
        return f"{DataClient.PATH_PUBLISH_BASE}/{subject}"

    @staticmethod
    def __subscribe_paths(stream: str, consumer: str) -> Dict[str, str]:
        """Helper function to compute the endpoint path related to subscription"""
        base_path = f"{DataClient.PATH_SUBSCRIBE_BASE}/{stream}/consumer/{consumer}"
        return {"base": base_path, "push_sub": base_path, "ack": f"{base_path}/ack"}

    def __init__(self, api_client: client.APIClient):
        """Constructor

        :param api_client: base client object for interacting with httpmq
        """
        self.client = api_client

    async def disconnect(self):
        """Disconnect from the server"""
        await self.client.disconnect()

    async def ready(self, context: RequestContext):
        """Check whether the httpmq dataplane API is ready. Raise exception if not.

        :param context: the caller context
        """
        resp = await self.client.get(path=DataClient.PATH_READY, context=context)
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
        # Base64 encode the message
        encoded = base64.b64encode(message)
        resp = await self.client.post(
            path=DataClient.__publish_path(subject), context=context, body=encoded
        )
        # Process the response body
        parsed = GoutilsRestAPIBaseResponse.from_dict(json.loads(resp.content))
        if not parsed.success:
            raise HttpmqAPIError.from_rest_base_api_response(parsed)
        return parsed.request_id

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
        payload = json.dumps(
            DataplaneAckSeqNum(consumer=consumer_seq, stream=stream_seq).to_dict()
        ).encode("utf-8")
        resp = await self.client.post(
            path=(
                DataClient.__subscribe_paths(stream=stream, consumer=consumer)["ack"]
            ),
            context=context,
            body=payload,
        )
        # Process the response body
        parsed = GoutilsRestAPIBaseResponse.from_dict(json.loads(resp.content))
        if not parsed.success:
            raise HttpmqAPIError.from_rest_base_api_response(parsed)
        return parsed.request_id

    async def send_ack_simple(
        self, original_msg: ReceivedMessage, context: RequestContext
    ) -> str:
        """Send a message ACK for an associated JetStream message

        This is a wrapper around `send_ack`.

        :param orignal_msg: the received JetStream message
        :param context: the caller context
        :return: request ID in the response
        """
        return await self.send_ack(
            stream=original_msg.stream,
            stream_seq=original_msg.stream_seq,
            consumer=original_msg.consumer,
            consumer_seq=original_msg.consumer_seq,
            context=context,
        )

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
        # Update request context with additional query parameters
        context.add_param(param_name="subject_name", param_value=subject_filter)
        if max_msg_inflight is not None:
            context.add_param(
                param_name="max_msg_inflight", param_value=max_msg_inflight
            )
        if delivery_group is not None:
            context.add_param(param_name="delivery_group", param_value=delivery_group)

        # URL path for the push subscription
        target_path = DataClient.__subscribe_paths(stream=stream, consumer=consumer)[
            "push_sub"
        ]

        # Callback for processing the byte string
        assemble_buffer = DataClient.RxMessageSplitter()

        async def process_stream_segment(
            msg: Union[
                client.APIClient.StreamDataSegment, client.APIClient.StreamDataEnd
            ]
        ):
            """Helper function to marshal the bytes stream being received"""
            if isinstance(msg, client.APIClient.StreamDataEnd):
                LOG.debug("[%s] Push-subscribe loop ended", context.request_id)
                return
            if isinstance(msg, client.APIClient.StreamDataSegment):
                # Process the message byte
                messages = assemble_buffer.process_new_segment(msg.data)
                for one_msg in messages:
                    # Decode each message
                    parsed = ApisAPIRestRespDataMessage.from_dict(one_msg)
                    if not parsed.success:
                        error = HttpmqAPIError.from_rest_base_api_response(parsed)
                        await forward_data_cb(error)
                        raise error
                    LOG.debug(
                        "[%s] Push-subscribe received message [S:%d, C:%d]",
                        parsed.request_id,
                        parsed.sequence.stream,
                        parsed.sequence.consumer,
                    )
                    # Perform Base64 decode
                    decoded = base64.b64decode(parsed.b64_msg)
                    # Repackage the message
                    message = ReceivedMessage(
                        stream=parsed.stream,
                        stream_seq=parsed.sequence.stream,
                        consumer=parsed.consumer,
                        consumer_seq=parsed.sequence.consumer,
                        subject=parsed.subject,
                        request_id=parsed.request_id,
                        message=decoded,
                    )
                    await forward_data_cb(message)
                return
            raise HttpmqInternalError(
                request_id=context.request_id,
                message=(
                    f"`APIClient.get_sse` returned unexpected result type: {type(msg)}"
                ),
            )

        resp = await self.client.get_sse(
            path=target_path,
            context=context,
            stop_loop=stop_loop,
            forward_data_cb=process_stream_segment,
            loop_interval_sec=loop_interval_sec,
        )
        if resp.status != HTTPStatus.OK:
            raise HttpmqAPIError.from_rest_base_api_response(
                GoutilsRestAPIBaseResponse.from_dict(json.loads(resp.content))
            )

        LOG.debug("[%s] Leaving push-subscribe runner", context.request_id)
        return context.request_id

    class RxMessageSplitter:
        """
        Support class for taking the text stream from the push subscription endpoint, and
        separate that out into individual messages
        """

        def __init__(self):
            """Constructor"""
            self.left_over = None

        def process_new_segment(self, stream_chunk: bytes) -> List[Dict[str, object]]:
            """Given a new stream chunk, process a list of parsed DICT

            :param stream_chunk: new message chunk
            :return: list of parsed DICTs
            """
            if not stream_chunk:
                return []

            # Split the chunk by NL
            lines = stream_chunk.decode("utf-8").split("\n")
            if len(lines) == 0:
                return []

            parsed_lines = []
            # Process each line
            for one_line in lines:
                to_process = one_line
                # If there were leftovers, combine the current one with leftover
                if self.left_over is not None:
                    to_process = self.left_over + one_line
                    self.left_over = None
                if not to_process:
                    continue
                try:
                    parsed = json.loads(to_process)
                    parsed_lines.append(parsed)
                except json.decoder.JSONDecodeError:
                    # Parse failure, assume incomplete
                    self.left_over = to_process

            return parsed_lines
