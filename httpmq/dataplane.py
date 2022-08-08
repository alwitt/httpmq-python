"""Wrapper object for operating the httpmq dataplane API"""

# pylint: disable=too-many-arguments
# pylint: disable=too-few-public-methods
# pylint: disable=too-many-locals

import base64
import json
import traceback
from typing import Dict, List
import urllib3
from httpmq.core import ApiClient
from httpmq.core.api.dataplane_api import DataplaneApi
from httpmq.core.models import (
    GoutilsRestAPIBaseResponse,
    DataplaneAckSeqNum,
)
from .common import APICallContext, HttpmqAPIError


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

    def publish(self, subject: str, message: bytes, ctxt: APICallContext) -> str:
        """Publishes a message under a subject

        :param subject: the subject to publish under
        :param message: the message to publish
        :param ctxt: the caller context
        :return: request ID in the response
        """
        # Base64 encode message
        encoded_msg = base64.b64encode(message).decode("utf-8")
        response: GoutilsRestAPIBaseResponse = (
            self.client.v1_data_subject_subject_name_post(
                subject_name=subject,
                message=encoded_msg,
                httpmq_request_id=ctxt.request_id,
                async_req=False,
                _request_timeout=ctxt.request_timeout_sec,
                _request_auths=ctxt.auth_param,
            )
        )
        # Failed
        if not response.success:
            raise HttpmqAPIError.new_error(response)
        return response.request_id

    def send_ack(
        self,
        stream: str,
        stream_seq: int,
        consumer: str,
        consumer_seq: int,
        ctxt: APICallContext,
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
        :param ctxt: the caller context
        :return: request ID in the response
        """
        response: GoutilsRestAPIBaseResponse = (
            self.client.v1_data_stream_stream_name_consumer_consumer_name_ack_post(
                stream_name=stream,
                consumer_name=consumer,
                sequence_num=DataplaneAckSeqNum(
                    stream=stream_seq, consumer=consumer_seq
                ),
                httpmq_request_id=ctxt.request_id,
                async_req=False,
                _request_timeout=ctxt.request_timeout_sec,
                _request_auths=ctxt.auth_param,
            )
        )
        # Failed
        if not response.success:
            raise HttpmqAPIError.new_error(response)
        return response.request_id

    def push_subscribe(
        self,
        stream: str,
        consumer: str,
        subject_filter: str,
        process_rx_msg_cb,
        ctxt: APICallContext,
        max_msg_inflight: int = None,
        delivery_group: str = None,
    ) -> str:
        """Start a push subscription for a consumer on a stream

        This is a blocking function which only exits when either
          * Connection breaks
          * Server closes the connection

        :param stream: target stream
        :param consumer: consumer name
        :param subject_filter: subscribe for message which subject matches the filter
        :param process_rx_msg_cb: callback function for handling a received message
        :param ctxt: the caller context
        :param max_msg_inflight: the max number of inflight messages if provided
        :param delivery_group: the delivery group the consumer belongs to if the consumer
            uses one
        :return: request ID in the response
        """

        # Operate the urllib3 requests directly

        # Target URL
        base_url = self.client.api_client.configuration.host
        subscribe_url = f"{base_url}/v1/data/stream/{stream}/consumer/{consumer}"

        # Query parameters
        query_params = {"subject_name": subject_filter}
        if max_msg_inflight is not None:
            query_params["max_msg_inflight"] = max_msg_inflight
        if delivery_group is not None:
            query_params["delivery_group"] = delivery_group

        # Header parameters
        header_params = {"Httpmq-Request-ID": ctxt.request_id}
        for one_auth_param in ctxt.auth_param:
            header_params[one_auth_param["key"]] = one_auth_param["value"]

        http = self.client.api_client.rest_client.pool_manager

        # Make request
        req = http.request(
            "GET",
            subscribe_url,
            fields=query_params,
            headers=header_params,
            preload_content=False,
            retries=False,
            timeout=urllib3.Timeout(total=None),
        )

        # Buffer for processing a stream of
        stream_buffer = RxMessageSplitter()

        try:
            for chunk in req.stream():
                parsed_lines = stream_buffer.process_new_segment(chunk)
                # Parse the parsed lines
                for one_parsed_line in parsed_lines:
                    # layout the message pieces
                    msg_consumer = one_parsed_line["consumer"]
                    msg_consumer_seq = one_parsed_line["sequence"]["consumer"]
                    msg_stream = one_parsed_line["stream"]
                    msg_stream_seq = one_parsed_line["sequence"]["stream"]
                    msg_request_id = one_parsed_line["request_id"]
                    msg_subject = one_parsed_line["subject"]
                    msg_body = one_parsed_line["b64_msg"]
                    # base64 decode the message
                    original_body = base64.b64decode(msg_body)
                    # Package the message
                    message = ReceivedMessage(
                        stream=msg_stream,
                        stream_seq=msg_stream_seq,
                        consumer=msg_consumer,
                        consumer_seq=msg_consumer_seq,
                        subject=msg_subject,
                        request_id=msg_request_id,
                        message=original_body,
                    )
                    # Pass on the message
                    process_rx_msg_cb(message)
        except Exception as err:
            raise HttpmqAPIError(
                request_id=ctxt.request_id,
                status_code=req.status,
                message="push-subscription read error",
                detail="".join(
                    traceback.format_exception(type(err), err, err.__traceback__)
                ),
            ) from err
        finally:
            req.release_conn()

        return ctxt.request_id
